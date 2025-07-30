import json
import logging
import os
import time
import uuid
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from confluent_kafka import Producer
from matrice.deploy.client.client import MatriceDeployClient
from matrice.deploy.client.streaming_gateway.streaming_gateway_utils import (
    InputConfig,
    OutputConfig,
    InputType,
    OutputType,
    ModelInputType
)


from matrice.deploy.utils.post_processing import PostProcessor


class StreamingGateway:
    """Simplified streaming gateway that leverages MatriceDeployClient's capabilities.
    
    Supports both frame-based streaming (sending individual images) and video-based
    streaming (sending video chunks) based on the model_input_type configuration.
    
    Now includes optional post-processing capabilities for model results.
    
    Example usage:
        # Frame-based streaming (default)
        frame_input = create_camera_frame_input(camera_index=0, fps=30)
        
        # Video-based streaming (duration-based chunks)
        video_input = create_camera_video_input(
            camera_index=0, 
            fps=30, 
            video_duration=5.0,  # 5-second chunks
            video_format="mp4"
        )
        
        output_config = create_file_output("./results")
        
        gateway = StreamingGateway(
            session=session,
            deployment_id="your_deployment_id",
            inputs_config=[video_input],
            output_config=output_config
        )
        
        gateway.start_streaming()
    """

    def __init__(
        self,
        session,
        deployment_id: str = None,
        inputs_config: List[InputConfig] = None,
        output_config: OutputConfig = None,
        deployment_config: Dict = None,
        auth_key: str = None,
        consumer_group_id: str = None,
        result_callback: Optional[Callable] = None,
        strip_input_from_result: bool = True,
    ):
        """Initialize StreamingGateway.

        Args:
            session: Session object for authentication
            deployment_id: ID of existing deployment (optional if deployment_config provided)
            inputs_config: Multiple input configurations (alternative to input_config)
            output_config: Output configuration
            deployment_config: Configuration for creating new deployment
            auth_key: Authentication key for deployment
            consumer_group_id: Kafka consumer group ID
            result_callback: Optional callback function for processing results
            strip_input_from_result: Whether to remove 'input' field from results to save space
        """
        if not session:
            raise ValueError("Session is required")

        self.session = session
        self.rpc = self.session.rpc
        self.auth_key = auth_key
        self.deployment_id = deployment_id
        self.deployment_config = deployment_config
        self.strip_input_from_result = strip_input_from_result

        # Validate inputs
        if not (self.deployment_id or self.deployment_config):
            raise ValueError(
                "Either deployment_id or deployment_config must be provided"
            )

        if not inputs_config:
            raise ValueError("At least one input configuration is required")

        self.inputs_config = (
            inputs_config if isinstance(inputs_config, list) else [inputs_config]
        )

        # Validate each input config
        for i, config in enumerate(self.inputs_config):
            if not isinstance(config, InputConfig):
                raise ValueError(f"Input config {i} must be an InputConfig instance")

        self.output_config = output_config
        self.consumer_group_id = consumer_group_id
        self.result_callback = result_callback
        self.kafka_producer = None

        # Initialize client
        self.client = None
        self._initialize_client()

        # State management with proper synchronization
        self.is_streaming = False
        self.result_thread: Optional[threading.Thread] = None
        self._stop_streaming = threading.Event()
        self._file_counter = 0
        self._state_lock = threading.RLock()

        # Initialize post-processing
        self.post_processor = None
        if self.output_config and self.output_config.apply_post_processing:
            self._setup_post_processing()

        # Statistics
        self.stats = {
            "start_time": None,
            "results_received": 0,
            "results_post_processed": 0,
            "post_processing_errors": 0,
            "errors": 0,
            "last_error": None,
            "last_error_time": None,
        }

        # Setup output
        self._setup_output()

        logging.info(
            f"StreamingGateway initialized for deployment {self.deployment_id}"
        )

    def _initialize_client(self):
        """Initialize the deployment client."""
        try:
            if self.deployment_id:
                # Use existing deployment
                self.client = MatriceDeployClient(
                    session=self.session,
                    deployment_id=self.deployment_id,
                    auth_key=self.auth_key,
                    consumer_group_id=self.consumer_group_id,
                )
            else:
                # Create new deployment
                self._create_deployment()
                if self.deployment_id:
                    self.client = MatriceDeployClient(
                        session=self.session,
                        deployment_id=self.deployment_id,
                        auth_key=self.auth_key,
                        consumer_group_id=self.consumer_group_id,
                    )
                else:
                    raise RuntimeError("Failed to create deployment")
        except Exception as exc:
            logging.error(f"Failed to initialize client: {exc}")
            raise

    def _create_deployment(self):
        """Create a new deployment."""
        default_config = {
            "isKafkaEnabled": True,
            "deploymentName": f"streaming_gateway_{uuid.uuid4().hex[:8]}",
            "shutdownThreshold": 60,
            "checkpointType": "predefined",
            "modelType": "pretrained",
            "checkpointValue": "yolov10x",
            "_idModel": "000000000000000000000000",
            "modelFamilyName": "YOLOv10",
            "modelKey": "yolov10x",
            "dataset": "COCO",
            "gpuRequired": True,
            "instanceRange": [1, 1],
            "autoShutdown": True,
            "autoScale": False,
            "customSchedule": False,
            "serverType": "fastapi",
            "scheduleDeployment": [],
            "deploymentType": "regular",
            "computeAlias": "",
        }

        if self.deployment_config:
            default_config.update(self.deployment_config)

        try:
            resp = self.rpc.post("/v1/deployment", payload=default_config)

            if resp and resp.get("success"):
                self.deployment_id = resp["data"]["_id"]
                logging.info(f"Created deployment: {self.deployment_id}")
            else:
                raise RuntimeError(f"Failed to create deployment: {resp}")
        except Exception as exc:
            logging.error(f"Error creating deployment: {exc}")
            raise RuntimeError(f"Failed to create deployment: {str(exc)}")

    def _setup_output(self):
        """Setup output configurations."""
        if not self.output_config:
            return

        try:
            # Setup file output
            if self.output_config.type in [OutputType.FILE, OutputType.BOTH]:
                if self.output_config.file_config:
                    os.makedirs(self.output_config.file_config.directory, exist_ok=True)

            # Setup Kafka output
            if self.output_config.type in [OutputType.KAFKA, OutputType.BOTH]:
                if self.output_config.kafka_config:
                    self._setup_kafka_producer()
        except Exception as exc:
            logging.error(f"Error setting up output: {exc}")
            raise

    def _setup_kafka_producer(self):
        """Setup Kafka producer for custom output."""
        try:
            kafka_config = self.output_config.kafka_config
            producer_config = {
                "bootstrap.servers": kafka_config.bootstrap_servers,
                "acks": "all",
                "retries": 3,
                "batch.size": 16384,
                "linger.ms": 1,
                "buffer.memory": 33554432,
            }

            # Add custom producer config if provided
            if kafka_config.producer_config:
                producer_config.update(kafka_config.producer_config)

            self.kafka_producer = Producer(producer_config)
            logging.info("Kafka producer initialized successfully")
        except Exception as exc:
            logging.error(f"Failed to setup Kafka producer: {exc}")
            raise

    def _setup_post_processing(self):
        """Setup post-processing capabilities."""
        if not self.output_config.post_processing_config:
            raise ValueError("Post-processing configuration is required when apply_post_processing is True")
        
        try:
            # Initialize PostProcessor with the configuration
            self.post_processor = PostProcessor(
                config=self.output_config.post_processing_config,
                index_to_category=self.output_config.post_processing_config.index_to_category,
                map_index_to_category=self.output_config.post_processing_config.map_index_to_category
            )
            logging.info("Post-processing initialized successfully")
        except Exception as exc:
            logging.error(f"Failed to setup post-processing: {exc}")
            raise

    def _apply_post_processing(self, result: Dict) -> Dict:
        """Apply post-processing to a result.
        
        Args:
            result: Raw result from the model
            
        Returns:
            Dict containing both original and processed results
        """
        if not self.post_processor:
            return result
        
        try:
            # Extract the model output from the result
            model_output = result.get('result', result)
            
            # Apply post-processing
            processed_result = self.post_processor.process(model_output)
            
            # Update statistics
            with self._state_lock:
                self.stats["results_post_processed"] += 1
            
            # Create enhanced result
            enhanced_result = result.copy()
            enhanced_result['post_processing_applied'] = True
            enhanced_result['post_processing_result'] = processed_result
            
            # Optionally keep original result
            if self.output_config.save_original_results:
                enhanced_result['original_result'] = result.get('result', result)
            else:
                # Replace the result with processed data
                enhanced_result['result'] = processed_result.get('processed_data', model_output)
            
            return enhanced_result
            
        except Exception as exc:
            logging.error(f"Post-processing failed: {exc}")
            with self._state_lock:
                self.stats["post_processing_errors"] += 1
                self.stats["last_error"] = f"Post-processing error: {str(exc)}"
                self.stats["last_error_time"] = time.time()
            
            # Return original result with error information
            error_result = result.copy()
            error_result['post_processing_applied'] = False
            error_result['post_processing_error'] = str(exc)
            return error_result

    def wait_for_deployment(self, timeout: int = 600) -> bool:
        """Wait for deployment to be ready.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if deployment is ready, False if timeout
        """
        if not self.client:
            return False

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if self.client.is_healthy():
                    logging.info("Deployment is ready for streaming")
                    return True

                logging.debug("Deployment not ready yet, waiting...")
                time.sleep(10)

            except Exception as e:
                logging.debug(f"Deployment check failed: {e}")
                time.sleep(10)

        logging.error(f"Deployment not ready after {timeout} seconds")
        return False

    def start_streaming(self) -> bool:
        """Start streaming using MatriceDeployClient's built-in capabilities.

        Returns:
            bool: True if streaming started successfully, False otherwise
        """
        with self._state_lock:
            if self.is_streaming:
                logging.warning("Streaming is already active")
                return False

            if not self.client:
                logging.error("No client available for streaming")
                return False

        # Wait for deployment to be ready
        if not self.wait_for_deployment():
            logging.error("Deployment is not available for streaming")
            return False

        # Start streaming for each input
        started_streams = []
        try:
            for i, input_config in enumerate(self.inputs_config):
                # Convert input source based on type
                if input_config.type == InputType.CAMERA:
                    input_source = int(input_config.source)
                else:
                    input_source = str(input_config.source)

                stream_key = input_config.stream_key or f"stream_{i}"

                # Choose streaming method based on model input type
                if input_config.model_input_type == ModelInputType.VIDEO:
                    # Start video streaming
                    success = self.client.start_background_video_stream(
                        input=input_source,
                        fps=input_config.fps,
                        stream_key=stream_key,
                        quality=input_config.quality,
                        width=input_config.width,
                        height=input_config.height,
                        video_duration=input_config.video_duration,
                        max_frames=input_config.max_frames,
                        video_format=input_config.video_format,
                    )
                    logging.info(f"Started video streaming for input {input_config.source} "
                               f"(duration: {input_config.video_duration}s, "
                               f"max_frames: {input_config.max_frames}, "
                               f"format: {input_config.video_format})")
                else:
                    # Start frame streaming (default)
                    success = self.client.start_background_stream(
                        input=input_source,
                        fps=input_config.fps,
                        stream_key=stream_key,
                        quality=input_config.quality,
                        width=input_config.width,
                        height=input_config.height,
                    )
                    logging.info(f"Started frame streaming for input {input_config.source}")

                if not success:
                    logging.error(
                        f"Failed to start streaming for input {input_config.source}"
                    )
                    # Stop already started streams
                    if started_streams:
                        logging.info("Stopping already started streams due to failure")
                        self.client.stop_streaming()
                    return False

                started_streams.append(stream_key)

            with self._state_lock:
                self._stop_streaming.clear()
                self.is_streaming = True
                self.stats["start_time"] = time.time()

            # Start result consumption thread if we have output config or callback
            if self.output_config or self.result_callback:
                self.result_thread = threading.Thread(
                    target=self._consume_results, daemon=True, name="ResultConsumer"
                )
                self.result_thread.start()

            logging.info(
                f"Started streaming successfully with {len(self.inputs_config)} inputs"
            )
            return True

        except Exception as exc:
            logging.error(f"Error starting streaming: {exc}")
            # Clean up on error
            try:
                if self.client:
                    self.client.stop_streaming()
            except Exception as cleanup_exc:
                logging.error(f"Error during cleanup: {cleanup_exc}")
            return False

    def _consume_results(self):
        """Consume and process results from the deployment."""
        logging.info("Starting result consumption thread")

        while not self._stop_streaming.is_set():
            try:
                result = self.client.consume_result(timeout=1.0)

                if not result:
                    continue

                # Remove input field if configured to do so
                if self.strip_input_from_result and "input" in result["value"]:
                    del result["value"]["input"]

                with self._state_lock:
                    self.stats["results_received"] += 1

                # Apply post-processing if configured
                processed_result = result
                if self.output_config and self.output_config.apply_post_processing:
                    processed_result = self._apply_post_processing(result)

                # Process result based on output configuration
                if self.output_config:
                    try:
                        if self.output_config.type in [OutputType.FILE, OutputType.BOTH]:
                            self._save_result_to_file(processed_result)

                        if self.output_config.type in [OutputType.KAFKA, OutputType.BOTH]:
                            self._send_result_to_kafka(processed_result)

                    except Exception as output_exc:
                        logging.error(f"Error processing output: {output_exc}")
                        with self._state_lock:
                            self.stats["errors"] += 1
                            self.stats["last_error"] = str(output_exc)
                            self.stats["last_error_time"] = time.time()

                # Call custom callback if provided (use processed result)
                if self.result_callback:
                    try:
                        self.result_callback(processed_result)
                    except Exception as callback_exc:
                        logging.error(f"Error in result callback: {callback_exc}")
                        with self._state_lock:
                            self.stats["errors"] += 1
                            self.stats["last_error"] = str(callback_exc)
                            self.stats["last_error_time"] = time.time()

            except Exception as e:
                logging.error(f"Error in result consumption: {e}")
                with self._state_lock:
                    self.stats["errors"] += 1
                    self.stats["last_error"] = str(e)
                    self.stats["last_error_time"] = time.time()

                # Add a small delay to prevent tight error loops
                time.sleep(0.1)

        logging.info("Result consumption thread stopped")

    def _save_result_to_file(self, result: Dict):
        """Save result to file."""
        if not self.output_config.file_config:
            return

        try:
            stream_key = result["value"].get("stream_key", "default_stream")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]

            filename = self.output_config.file_config.filename_pattern.format(
                frame_number=result.get("frame_number", self._file_counter), 
                stream_key=stream_key,
                timestamp=timestamp
            )

            filepath = os.path.join(self.output_config.file_config.directory, filename)

            # Add metadata
            result_with_metadata = {
                "timestamp": timestamp,
                "deployment_id": self.deployment_id,
                "stream_key": stream_key,
                "result": result,
            }

            # Write atomically by using a temporary file
            temp_filepath = filepath + ".tmp"
            try:
                with open(temp_filepath, "w") as f:
                    json.dump(result_with_metadata, f, indent=2, default=str)  # Use default=str for non-serializable objects
            except (TypeError, ValueError) as json_err:
                logging.error(f"JSON serialization error: {json_err}")
                # Try to save a simplified version
                simplified_result = {
                    "timestamp": timestamp,
                    "deployment_id": str(self.deployment_id),
                    "stream_key": str(stream_key),
                    "result": str(result),  # Convert to string as fallback
                    "json_error": str(json_err)
                }
                with open(temp_filepath, "w") as f:
                    json.dump(simplified_result, f, indent=2)

            os.rename(temp_filepath, filepath)
            self._file_counter += 1

            # Cleanup old files if needed
            if (
                self.output_config.file_config.max_files
                and self._file_counter % 10 == 0
            ):
                self._cleanup_old_files()

        except Exception as e:
            logging.error(f"Failed to save result to file: {e}")
            logging.exception("File save error details:")
            raise

    def _cleanup_old_files(self):
        """Remove old result files if exceeding max_files limit."""
        try:
            directory = self.output_config.file_config.directory
            max_files = self.output_config.file_config.max_files

            files = []
            for filename in os.listdir(directory):
                if filename.endswith(".json") and not filename.endswith(".tmp"):
                    filepath = os.path.join(directory, filename)
                    if os.path.isfile(filepath):
                        files.append((filepath, os.path.getctime(filepath)))

            # Sort by creation time (oldest first)
            files.sort(key=lambda x: x[1])

            # Remove oldest files if exceeding limit
            while len(files) >= max_files:
                filepath, _ = files.pop(0)
                try:
                    os.remove(filepath)
                    logging.debug(f"Removed old result file: {filepath}")
                except Exception as e:
                    logging.warning(f"Failed to remove old file {filepath}: {e}")
        except Exception as e:
            logging.warning(f"Error during file cleanup: {e}")

    def _send_result_to_kafka(self, result: Dict):
        """Send result to custom Kafka topic."""
        if not self.kafka_producer or not self.output_config.kafka_config:
            return

        try:
            message = {
                "timestamp": datetime.now().isoformat(),
                "deployment_id": self.deployment_id,
                "result": result,
            }

            key = result.get(self.output_config.kafka_config.key_field or "key")

            try:
                # Attempt JSON serialization
                message_json = json.dumps(message, default=str)  # Use default=str for non-serializable objects
            except (TypeError, ValueError) as json_err:
                logging.error(f"JSON serialization error for Kafka: {json_err}")
                # Create a simplified message
                simplified_message = {
                    "timestamp": datetime.now().isoformat(),
                    "deployment_id": str(self.deployment_id),
                    "result": str(result),  # Convert to string as fallback
                    "json_error": str(json_err)
                }
                message_json = json.dumps(simplified_message)

            self.kafka_producer.produce(
                topic=self.output_config.kafka_config.topic,
                key=str(key) if key else None,
                value=message_json.encode("utf-8"),
            )
            self.kafka_producer.poll(0)  # Non-blocking poll

        except Exception as e:
            logging.error(f"Failed to send result to Kafka: {e}")
            logging.exception("Kafka send error details:")
            raise

    def stop_streaming(self):
        """Stop all streaming operations."""
        with self._state_lock:
            if not self.is_streaming:
                logging.warning("Streaming is not active")
                return

            logging.info("Stopping streaming...")
            self._stop_streaming.set()
            self.is_streaming = False

        # Stop client streaming
        if self.client:
            try:
                self.client.stop_streaming()
            except Exception as exc:
                logging.error(f"Error stopping client streaming: {exc}")

        # Wait for result thread to finish
        if self.result_thread and self.result_thread.is_alive():
            self.result_thread.join(timeout=10.0)
            if self.result_thread.is_alive():
                logging.warning("Result thread did not stop gracefully")

        self.result_thread = None

        # Flush Kafka producer
        if self.kafka_producer:
            try:
                self.kafka_producer.flush(timeout=5.0)
            except Exception as exc:
                logging.error(f"Error flushing Kafka producer: {exc}")

        logging.info("Streaming stopped")

    def get_statistics(self) -> Dict:
        """Get streaming statistics.
        
        Returns:
            Dict with streaming statistics
        """
        with self._state_lock:
            stats = self.stats.copy()

        if stats["start_time"]:
            runtime = time.time() - stats["start_time"]
            stats["runtime_seconds"] = runtime
            if runtime > 0:
                stats["results_per_second"] = stats["results_received"] / runtime
            else:
                stats["results_per_second"] = 0
        else:
            stats["runtime_seconds"] = 0
            stats["results_per_second"] = 0

        return stats

    def get_config(self) -> Dict:
        """Get current configuration.
        
        Returns:
            Dict with current configuration
        """
        return {
            "deployment_id": self.deployment_id,
            "inputs_config": [config.to_dict() for config in self.inputs_config],
            "output_config": self.output_config.to_dict() if self.output_config else None,
            "consumer_group_id": self.consumer_group_id,
            "strip_input_from_result": self.strip_input_from_result,
        }

    def save_config(self, filepath: str):
        """Save current configuration to file.
        
        Args:
            filepath: Path to save configuration
        """
        config = self.get_config()
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)

    @classmethod
    def load_config(
        cls, filepath: str, session=None, auth_key: str = None
    ) -> "StreamingGateway":
        """Load configuration from file and create StreamingGateway.
        
        Args:
            filepath: Path to configuration file
            session: Session object (required)
            auth_key: Authentication key
            
        Returns:
            StreamingGateway instance
        """
        if not session:
            raise ValueError("Session is required")

        with open(filepath, 'r') as f:
            config = json.load(f)

        inputs_config = [InputConfig.from_dict(input_cfg) for input_cfg in config["inputs_config"]]
        output_config = OutputConfig.from_dict(config["output_config"]) if config["output_config"] else None

        return cls(
            session=session,
            deployment_id=config["deployment_id"],
            inputs_config=inputs_config,
            output_config=output_config,
            auth_key=auth_key,
            consumer_group_id=config.get("consumer_group_id"),
            strip_input_from_result=config.get("strip_input_from_result", True),
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_streaming()

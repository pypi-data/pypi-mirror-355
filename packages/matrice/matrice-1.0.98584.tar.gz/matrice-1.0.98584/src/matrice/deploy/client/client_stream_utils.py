from typing import Dict, Optional, Union
import base64
import logging
import cv2
import threading
import time
import tempfile
import os
from matrice.deploy.utils.kafka_utils import MatriceKafkaDeployment


class ClientStreamUtils:
    def __init__(
        self,
        session,
        deployment_id: str,
        consumer_group_id: str = None,
        consumer_group_instance_id: str = None,
    ):
        """Initialize ClientStreamUtils.

        Args:
            session: Session object for making RPC calls
            deployment_id: ID of the deployment
            consumer_group_id: Kafka consumer group ID
            consumer_group_instance_id: Unique consumer group instance ID to prevent rebalancing
        """
        self.streaming_threads = []
        self.session = session
        self.deployment_id = deployment_id
        self.kafka_deployment = MatriceKafkaDeployment(
            self.session,
            self.deployment_id,
            "client",
            consumer_group_id,
            consumer_group_instance_id,
        )
        self.stream_support = self.kafka_deployment.setup_success
        self._stop_streaming = False

    def start_stream(
        self,
        input: Union[str, int],
        fps: int = 10,
        stream_key: Optional[str] = None,
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> bool:
        """Start a stream input to the Kafka stream.

        Args:
            input: Video path, webcam index, or camera URL
            fps: Frames per second to stream
            quality: JPEG compression quality (1-100, higher is better quality)
            width: Target frame width (None to keep original)
            height: Target frame height (None to keep original)
        """
        if not self.stream_support:
            logging.error(
                "Kafka stream support not available, Please check if Kafka is enabled in the deployment and reinitialize the client"
            )
            return False
        
        # Validate parameters
        if fps <= 0:
            logging.error("FPS must be positive")
            return False
        if quality < 1 or quality > 100:
            logging.error("Quality must be between 1 and 100")
            return False
        if width is not None and width <= 0:
            logging.error("Width must be positive")
            return False
        if height is not None and height <= 0:
            logging.error("Height must be positive")
            return False
            
        try:
            self._stream_inputs(
                input, fps, stream_key, quality=quality, width=width, height=height
            )
            return True
        except Exception as exc:
            logging.error("Failed to start streaming thread: %s", str(exc))
            return False
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt, stopping streaming")
            self.stop_streaming()
            return False

    def start_background_stream(
        self,
        input: Union[str, int],
        fps: int = 10,
        stream_key: Optional[str] = None,
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> bool:
        """Add a stream input to the Kafka stream.

        Args:
            input: Video path, webcam index, or camera URL
            fps: Frames per second to stream
            stream_key: Stream key for partitioning
            quality: JPEG compression quality (1-100, higher is better quality)
            width: Target frame width (None to keep original)
            height: Target frame height (None to keep original)

        Returns:
            bool: True if stream started successfully, False otherwise
        """
        if not self.stream_support:
            logging.error(
                "Kafka stream support not available, Please check if Kafka is enabled in the deployment and reinitialize the client"
            )
            return False
        
        # Validate parameters
        if fps <= 0:
            logging.error("FPS must be positive")
            return False
        if quality < 1 or quality > 100:
            logging.error("Quality must be between 1 and 100")
            return False
        if width is not None and width <= 0:
            logging.error("Width must be positive")
            return False
        if height is not None and height <= 0:
            logging.error("Height must be positive")
            return False
            
        try:
            thread = threading.Thread(
                target=self._stream_inputs,
                args=(input, fps, stream_key),
                kwargs={"quality": quality, "width": width, "height": height},
                daemon=True,
            )
            self.streaming_threads.append(thread)
            thread.start()
            return True
        except Exception as exc:
            logging.error("Failed to start streaming thread: %s", str(exc))
            return False

    def _stream_inputs(
        self,
        input: Union[str, int],
        fps: int = 10,
        stream_key: Optional[str] = None,
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> None:
        """Stream inputs from a video source to Kafka.

        Args:
            input: Video path, webcam index, or camera URL
            fps: Frames per second to stream
            stream_key: Stream key for partitioning
            quality: JPEG compression quality (1-100, higher is better quality)
            width: Target frame width (None to keep original)
            height: Target frame height (None to keep original)
        """
        # Validate quality parameter
        quality = max(1, min(100, quality))

        cap = None
        try:
            # Handle different input types
            if isinstance(input, int) or (isinstance(input, str) and input.isdigit()):
                # For webcam (e.g., camera 0)
                cap = cv2.VideoCapture(int(input) if isinstance(input, str) else input)
                logging.info(f"Opening webcam device: {input}")
            else:
                # For video file path or URL
                cap = cv2.VideoCapture(input)
                logging.info(f"Opening video source: {input}")

            # Check if camera/video opened successfully
            if not cap.isOpened():
                logging.error(f"Failed to open video source: {input}")
                raise RuntimeError(f"Failed to open video source: {input}")

            # Try to set properties for better performance if it's a camera
            if isinstance(input, int) or (isinstance(input, str) and input.isdigit()):
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering for real-time
                # Set resolution if specified
                if width is not None:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                if height is not None:
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            retry_count = 0
            max_retries = 3
            consecutive_failures = 0
            max_consecutive_failures = 10

            frame_interval = 1.0 / fps
            while not self._stop_streaming:
                start_time = time.time()

                # Read frame with retry logic
                ret, frame = cap.read()

                if not ret:
                    retry_count += 1
                    consecutive_failures += 1
                    logging.warning(
                        f"Failed to read frame, retry {retry_count}/{max_retries}"
                    )

                    if consecutive_failures >= max_consecutive_failures:
                        logging.error("Too many consecutive failures, stopping stream")
                        break

                    if retry_count >= max_retries:
                        if isinstance(input, int) or (
                            isinstance(input, str) and input.isdigit()
                        ):
                            # For cameras, try to reopen
                            logging.info("Attempting to reopen camera...")
                            cap.release()
                            time.sleep(1)  # Give camera time to reset
                            cap = cv2.VideoCapture(
                                int(input) if isinstance(input, str) else input
                            )
                            if not cap.isOpened():
                                logging.error(
                                    "Failed to reopen camera, stopping stream"
                                )
                                break
                            # Reapply resolution settings
                            if width is not None:
                                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                            if height is not None:
                                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                            retry_count = 0
                        else:
                            # For video files, we've reached the end
                            logging.info(f"End of stream reached for input: {input}")
                            break

                    time.sleep(0.1)  # Short delay before retry
                    continue

                # Reset counters on successful frame read
                retry_count = 0
                consecutive_failures = 0

                # Resize frame if dimensions are specified and different from current
                if width is not None or height is not None:
                    current_height, current_width = frame.shape[:2]
                    target_width = width if width is not None else current_width
                    target_height = height if height is not None else current_height

                    if target_width != current_width or target_height != current_height:
                        frame = cv2.resize(frame, (target_width, target_height))

                try:
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
                    _, buffer = cv2.imencode(".jpg", frame, encode_params)
                except Exception as encode_exc:
                    logging.warning(f"Failed to encode frame with quality {quality}, using default: {encode_exc}")
                    try:
                        _, buffer = cv2.imencode(".jpg", frame)
                    except Exception as fallback_exc:
                        logging.error(f"Failed to encode frame even with default settings: {fallback_exc}")
                        continue

                # Send frame to Kafka
                if not self.produce_request(buffer.tobytes(), stream_key):
                    logging.warning("Failed to produce frame to Kafka stream")

                # Calculate sleep time to maintain desired FPS
                processing_time = time.time() - start_time
                sleep_time = max(0, frame_interval - processing_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as exc:
            logging.error(f"Error in streaming thread: {str(exc)}")
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt, stopping streaming")
        finally:
            if cap is not None:
                cap.release()
                logging.info(f"Released video source: {input}")

    def stop_streaming(self) -> None:
        """Stop all streaming threads."""
        self._stop_streaming = True
        for thread in self.streaming_threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        self.streaming_threads = []
        self._stop_streaming = False
        logging.info("All streaming threads stopped")

    def produce_request(
        self, input: bytes, stream_key: Optional[str] = None, timeout: float = 60.0, metadata: Optional[Dict] = None
    ) -> bool:
        """Add a message to the Kafka stream.

        Args:
            input: Input to produce
            stream_key: Stream key for partitioning
            timeout: Maximum time to wait for message delivery in seconds
            metadata: Optional metadata to include with the message

        Returns:
            bool: True if successful, False otherwise

        Raises:
            RuntimeError: If producer is not initialized
            ValueError: If message is invalid
        """
        if not input:
            logging.error("Input cannot be empty")
            return False
            
        try:
            message = {
                "input": base64.b64encode(input).decode("utf-8"),
                "stream_key": stream_key,
                "metadata": metadata or {}
            }
            self.kafka_deployment.produce_message(
                message, timeout=timeout, key=stream_key
            )
            return True
        except Exception as exc:
            logging.error("Failed to add request to Kafka stream: %s", str(exc))
            return False

    def consume_result(self, timeout: float = 60.0) -> Optional[Dict]:
        """Consume the Kafka stream result.

        Args:
            timeout: Maximum time to wait for message in seconds

        Returns:
            Message dictionary if available, None if no message received
        """
        try:
            return self.kafka_deployment.consume_message(timeout)
        except Exception as exc:
            logging.error("Failed to consume Kafka stream result: %s", str(exc))
            return None

    async def async_produce_request(
        self, input: bytes, stream_key: Optional[str] = None, timeout: float = 60.0, metadata: Optional[Dict] = None
    ) -> bool:
        """Add a message to the Kafka stream asynchronously.

        Args:
            input: Input to produce
            stream_key: Stream key for partitioning
            timeout: Maximum time to wait for message delivery in seconds
            metadata: Optional metadata to include with the message

        Returns:
            bool: True if successful, False otherwise
        """
        if not input:
            logging.error("Input cannot be empty")
            return False
            
        try:
            message = {
                "input": base64.b64encode(input).decode("utf-8"),
                "stream_key": stream_key,
                "metadata": metadata or {}
            }
            await self.kafka_deployment.async_produce_message(
                message, timeout=timeout, key=stream_key
            )
            return True
        except Exception as exc:
            logging.error(
                "Failed to add request to Kafka stream asynchronously: %s", str(exc)
            )
            return False

    async def async_consume_result(self, timeout: float = 60.0) -> Optional[Dict]:
        """Consume the Kafka stream result asynchronously.

        Args:
            timeout: Maximum time to wait for message in seconds

        Returns:
            Message dictionary if available, None if no message received
        """
        try:
            return await self.kafka_deployment.async_consume_message(timeout)
        except Exception as exc:
            logging.error(
                "Failed to consume Kafka stream result asynchronously: %s", str(exc)
            )
            return None

    async def close(self) -> None:
        """Close all client connections including Kafka stream.

        Returns:
            None
        """
        errors = []

        # Stop all streaming threads
        try:
            self.stop_streaming()
        except Exception as exc:
            error_msg = f"Error stopping streaming threads: {str(exc)}"
            logging.error(error_msg)
            errors.append(error_msg)

        # Try to close Kafka connections
        try:
            await self.kafka_deployment.close()
            logging.info("Successfully closed Kafka connections")
        except Exception as exc:
            error_msg = f"Error closing Kafka connections: {str(exc)}"
            logging.error(error_msg)
            errors.append(error_msg)

        # Report all errors if any occurred
        if errors:
            error_summary = "\n".join(errors)
            logging.error("Errors occurred during close: %s", error_summary)

    def start_video_stream(
        self,
        input: Union[str, int],
        fps: int = 10,
        stream_key: Optional[str] = None,
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
        video_duration: Optional[float] = None,
        max_frames: Optional[int] = None,
        video_format: str = "mp4"
    ) -> bool:
        """Start a video stream sending video chunks instead of individual frames.

        Args:
            input: Video path, webcam index, or camera URL
            fps: Frames per second to capture and encode
            stream_key: Stream key for partitioning
            quality: Video compression quality (1-100, higher is better quality)
            width: Target frame width (None to keep original)
            height: Target frame height (None to keep original)
            video_duration: Duration of each video chunk in seconds (optional)
            max_frames: Maximum number of frames per video chunk (optional)
            video_format: Video format for encoding ('mp4', 'avi', 'webm')

        Returns:
            bool: True if stream started successfully, False otherwise
        """
        if not self.stream_support:
            logging.error(
                "Kafka stream support not available, Please check if Kafka is enabled in the deployment and reinitialize the client"
            )
            return False
        
        # Validate parameters
        if fps <= 0:
            logging.error("FPS must be positive")
            return False
        if quality < 1 or quality > 100:
            logging.error("Quality must be between 1 and 100")
            return False
        if width is not None and width <= 0:
            logging.error("Width must be positive")
            return False
        if height is not None and height <= 0:
            logging.error("Height must be positive")
            return False
        if video_duration is not None and video_duration <= 0:
            logging.error("Video duration must be positive")
            return False
        if max_frames is not None and max_frames <= 0:
            logging.error("Max frames must be positive")
            return False
        if video_format not in ['mp4', 'avi', 'webm']:
            logging.error("Video format must be one of: mp4, avi, webm")
            return False
            
        try:
            self._stream_video_chunks(
                input, fps, stream_key, quality=quality, width=width, height=height,
                video_duration=video_duration, max_frames=max_frames, video_format=video_format
            )
            return True
        except Exception as exc:
            logging.error("Failed to start video streaming thread: %s", str(exc))
            return False
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt, stopping video streaming")
            self.stop_streaming()
            return False

    def start_background_video_stream(
        self,
        input: Union[str, int],
        fps: int = 10,
        stream_key: Optional[str] = None,
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
        video_duration: Optional[float] = None,
        max_frames: Optional[int] = None,
        video_format: str = "mp4"
    ) -> bool:
        """Start a background video stream sending video chunks instead of individual frames.

        Args:
            input: Video path, webcam index, or camera URL
            fps: Frames per second to capture and encode
            stream_key: Stream key for partitioning
            quality: Video compression quality (1-100, higher is better quality)
            width: Target frame width (None to keep original)
            height: Target frame height (None to keep original)
            video_duration: Duration of each video chunk in seconds (optional)
            max_frames: Maximum number of frames per video chunk (optional)
            video_format: Video format for encoding ('mp4', 'avi', 'webm')

        Returns:
            bool: True if stream started successfully, False otherwise
        """
        if not self.stream_support:
            logging.error(
                "Kafka stream support not available, Please check if Kafka is enabled in the deployment and reinitialize the client"
            )
            return False
        
        # Validate parameters
        if fps <= 0:
            logging.error("FPS must be positive")
            return False
        if quality < 1 or quality > 100:
            logging.error("Quality must be between 1 and 100")
            return False
        if width is not None and width <= 0:
            logging.error("Width must be positive")
            return False
        if height is not None and height <= 0:
            logging.error("Height must be positive")
            return False
        if video_duration is not None and video_duration <= 0:
            logging.error("Video duration must be positive")
            return False
        if max_frames is not None and max_frames <= 0:
            logging.error("Max frames must be positive")
            return False
        if video_format not in ['mp4', 'avi', 'webm']:
            logging.error("Video format must be one of: mp4, avi, webm")
            return False
            
        try:
            thread = threading.Thread(
                target=self._stream_video_chunks,
                args=(input, fps, stream_key),
                kwargs={
                    "quality": quality, "width": width, "height": height,
                    "video_duration": video_duration, "max_frames": max_frames, 
                    "video_format": video_format
                },
                daemon=True,
            )
            self.streaming_threads.append(thread)
            thread.start()
            return True
        except Exception as exc:
            logging.error("Failed to start video streaming thread: %s", str(exc))
            return False

    def _stream_video_chunks(
        self,
        input: Union[str, int],
        fps: int = 10,
        stream_key: Optional[str] = None,
        quality: int = 95,
        width: Optional[int] = None,
        height: Optional[int] = None,
        video_duration: Optional[float] = None,
        max_frames: Optional[int] = None,
        video_format: str = "mp4"
    ) -> None:
        """Stream video chunks from a video source to Kafka.

        Args:
            input: Video path, webcam index, or camera URL
            fps: Frames per second to capture and encode
            stream_key: Stream key for partitioning
            quality: Video compression quality (1-100, higher is better quality)
            width: Target frame width (None to keep original)
            height: Target frame height (None to keep original)
            video_duration: Duration of each video chunk in seconds (optional)
            max_frames: Maximum number of frames per video chunk (optional)
            video_format: Video format for encoding ('mp4', 'avi', 'webm')
        """
        # Validate quality parameter
        quality = max(1, min(100, quality))

        cap = None
        try:
            # Handle different input types
            if isinstance(input, int) or (isinstance(input, str) and input.isdigit()):
                # For webcam (e.g., camera 0)
                cap = cv2.VideoCapture(int(input) if isinstance(input, str) else input)
                logging.info(f"Opening webcam device for video chunks: {input}")
            else:
                # For video file path or URL
                cap = cv2.VideoCapture(input)
                logging.info(f"Opening video source for video chunks: {input}")

            # Check if camera/video opened successfully
            if not cap.isOpened():
                logging.error(f"Failed to open video source: {input}")
                raise RuntimeError(f"Failed to open video source: {input}")

            # Try to set properties for better performance if it's a camera
            if isinstance(input, int) or (isinstance(input, str) and input.isdigit()):
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering for real-time
                # Set resolution if specified
                if width is not None:
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                if height is not None:
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            # Get actual frame dimensions
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Override with specified dimensions if provided
            if width is not None:
                actual_width = width
            if height is not None:
                actual_height = height

            # Set up video codec and writer parameters
            fourcc_map = {
                'mp4': cv2.VideoWriter_fourcc(*'mp4v'),
                'avi': cv2.VideoWriter_fourcc(*'XVID'),
                'webm': cv2.VideoWriter_fourcc(*'VP80')
            }
            fourcc = fourcc_map.get(video_format, cv2.VideoWriter_fourcc(*'mp4v'))

            # Calculate chunk limits
            if video_duration is not None:
                chunk_frames = int(fps * video_duration)
            elif max_frames is not None:
                chunk_frames = max_frames
            else:
                # Default to 5 seconds of video
                chunk_frames = int(fps * 5.0)

            retry_count = 0
            max_retries = 3
            chunk_count = 0
            consecutive_failures = 0
            max_consecutive_failures = 5

            while not self._stop_streaming:
                temp_path = None
                out = None
                try:
                    # Create a temporary file for this video chunk
                    with tempfile.NamedTemporaryFile(suffix=f'.{video_format}', delete=False) as temp_file:
                        temp_path = temp_file.name

                    # Create video writer for this chunk with optimized parameters
                    out = cv2.VideoWriter(temp_path, fourcc, fps, (actual_width, actual_height))
                    
                    if not out.isOpened():
                        logging.error(f"Failed to open video writer for {temp_path}")
                        consecutive_failures += 1
                        if consecutive_failures >= max_consecutive_failures:
                            logging.error("Too many consecutive video writer failures, stopping")
                            break
                        continue

                    consecutive_failures = 0  # Reset on success
                    frames_in_chunk = 0
                    chunk_start_time = time.time()

                    # Collect frames for this chunk
                    while frames_in_chunk < chunk_frames and not self._stop_streaming:
                        frame_start_time = time.time()
                        
                        # Read frame with retry logic
                        ret, frame = cap.read()

                        if not ret:
                            retry_count += 1
                            logging.warning(
                                f"Failed to read frame, retry {retry_count}/{max_retries}"
                            )

                            if retry_count >= max_retries:
                                if isinstance(input, int) or (
                                    isinstance(input, str) and input.isdigit()
                                ):
                                    # For cameras, try to reopen
                                    logging.info("Attempting to reopen camera...")
                                    cap.release()
                                    time.sleep(1)  # Give camera time to reset
                                    cap = cv2.VideoCapture(
                                        int(input) if isinstance(input, str) else input
                                    )
                                    if not cap.isOpened():
                                        logging.error(
                                            "Failed to reopen camera, stopping stream"
                                        )
                                        break
                                    # Reapply resolution settings
                                    if width is not None:
                                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                                    if height is not None:
                                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                                    retry_count = 0
                                else:
                                    # For video files, we've reached the end
                                    logging.info(f"End of stream reached for input: {input}")
                                    break

                            time.sleep(0.1)  # Short delay before retry
                            continue

                        # Reset retry counter on successful frame read
                        retry_count = 0

                        # Resize frame if dimensions are specified and different from current
                        if width is not None or height is not None:
                            current_height, current_width = frame.shape[:2]
                            target_width = width if width is not None else current_width
                            target_height = height if height is not None else current_height

                            if target_width != current_width or target_height != current_height:
                                frame = cv2.resize(frame, (target_width, target_height))

                        # Write frame to video file
                        out.write(frame)
                        frames_in_chunk += 1

                        # Maintain frame rate
                        frame_interval = 1.0 / fps
                        processing_time = time.time() - frame_start_time
                        sleep_time = max(0, frame_interval - processing_time)
                        if sleep_time > 0:
                            time.sleep(sleep_time)

                    # Finalize the video chunk
                    if out is not None:
                        out.release()
                        out = None

                    if frames_in_chunk > 0:
                        # Read the video file as bytes
                        try:
                            with open(temp_path, 'rb') as video_file:
                                video_bytes = video_file.read()

                            # Send video chunk to Kafka
                            chunk_count += 1
                            chunk_stream_key = f"{stream_key}_chunk_{chunk_count}" if stream_key else f"chunk_{chunk_count}"
                            
                            success = self.produce_request(
                                video_bytes, chunk_stream_key, 
                                metadata={
                                    "chunk_id": chunk_count,
                                    "frames_count": frames_in_chunk,
                                    "duration": time.time() - chunk_start_time,
                                    "video_format": video_format,
                                    "fps": fps,
                                    "width": actual_width,
                                    "height": actual_height
                                }
                            )
                            
                            if not success:
                                logging.warning(f"Failed to produce video chunk {chunk_count} to Kafka stream")
                            else:
                                logging.info(f"Successfully sent video chunk {chunk_count} with {frames_in_chunk} frames")

                        except Exception as e:
                            logging.error(f"Error reading video chunk file: {str(e)}")

                except Exception as chunk_exc:
                    logging.error(f"Error processing video chunk: {chunk_exc}")
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logging.error("Too many consecutive chunk processing failures, stopping")
                        break
                finally:
                    # Clean up resources
                    if out is not None:
                        try:
                            out.release()
                        except Exception as e:
                            logging.warning(f"Error releasing video writer: {e}")
                    
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.unlink(temp_path)
                        except Exception as e:
                            logging.warning(f"Failed to delete temporary file {temp_path}: {str(e)}")

                if retry_count >= max_retries:
                    break

        except Exception as exc:
            logging.error(f"Error in video streaming thread: {str(exc)}")
        except KeyboardInterrupt:
            logging.info("Keyboard interrupt, stopping video streaming")
        finally:
            if cap is not None:
                cap.release()
                logging.info(f"Released video source: {input}")

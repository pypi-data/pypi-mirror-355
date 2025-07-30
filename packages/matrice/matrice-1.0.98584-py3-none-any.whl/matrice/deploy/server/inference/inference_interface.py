from matrice.deploy.server.inference.model_manager import ModelManager
from matrice.deploy.utils.post_processing import PostProcessor
from typing import Dict, Any, Optional, Callable, Tuple
from matrice.action_tracker import ActionTracker
from datetime import datetime, timezone

class InferenceInterface:
    """Interface for proxying requests to model servers with optional post-processing."""

    def __init__(
        self,
        action_tracker: ActionTracker,
        model_manager: ModelManager,
        batch_size: int = 1,
        dynamic_batching: bool = False,
        post_processing_config: Optional[Dict[str, Any]] = None,
        custom_post_processing_fn: Optional[Callable] = None,
    ):
        self.batch_size = batch_size
        self.dynamic_batching = dynamic_batching
        self.model_manager = model_manager
        self.action_tracker = action_tracker
        self.post_processing_pipeline = None
        self.latest_inference_time = datetime.now(timezone.utc)
        if post_processing_config:
            self.post_processing_pipeline = PostProcessor(
                config=post_processing_config,
                index_to_category=self.action_tracker.get_index_to_category(),
            )
        self.custom_post_processing_fn = custom_post_processing_fn

    async def inference(
        self,
        input1,
        input2=None,
        extra_params=None,
        apply_post_processing: bool = False,
    ) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """Perform inference using the appropriate client with optional post-processing.

        Args:
            input1: Primary input data
            input2: Secondary input data (optional)
            extra_params: Additional parameters for inference (optional)
            apply_post_processing: Whether to apply post-processing

        Returns:
            Tuple containing (inference_result, post_processing_result).
            If post-processing is not applied, post_processing_result will be None.
            If post-processing is applied, post_processing_result contains the full post-processing metadata.

        Raises:
            ValueError: If client is not set up
            RuntimeError: If inference fails
        """
        self.latest_inference_time = datetime.now(timezone.utc)
        # Get raw inference results
        try:
            raw_results = await self.model_manager.inference(
                input1,
                input2,
                extra_params,
            )
        except Exception as e:
            raise RuntimeError(f"Model inference failed: {str(e)}") from e

        if not apply_post_processing:
            return raw_results, None

        # Apply post-processing
        post_processing_result = None
        processed_result = raw_results

        try:
            if self.post_processing_pipeline:
                post_processing_result = self.post_processing_pipeline.process(raw_results)
                # Extract processed data from the result
                if isinstance(post_processing_result, dict) and 'processed_data' in post_processing_result:
                    processed_result = post_processing_result['processed_data']
                else:
                    # If no 'processed_data' key, assume the entire result is the processed data
                    processed_result = post_processing_result.get('results', raw_results) if isinstance(post_processing_result, dict) else raw_results

            elif self.custom_post_processing_fn:
                post_processing_result = self.custom_post_processing_fn(raw_results)
                # Handle custom function output
                if isinstance(post_processing_result, tuple) and len(post_processing_result) == 2:
                    processed_result, post_processing_result = post_processing_result
                else:
                    processed_result = post_processing_result
                    post_processing_result = {"processed_data": processed_result}
            else:
                # No post-processing configured, return raw results
                return raw_results, None
        except Exception as e:
            # Log the error and return raw results with error info
            import logging
            logging.error(f"Post-processing failed: {str(e)}")
            post_processing_result = {
                "error": str(e),
                "status": "post_processing_failed",
                "processed_data": raw_results
            }
            processed_result = raw_results

        return processed_result, post_processing_result

    def get_latest_inference_time(self) -> datetime:
        """Get the latest inference time."""
        return self.latest_inference_time

# TODO: Add support for batching inference
# TODO: Add support for dynamic batching
# TODO: Add support for multi-model execution
# TODO: Add the Metrics and Logging
# TODO: Add the Auto Scale Up and Scale Down
# TODO: Add Buffer Cache for the inference
# TODO: Add post-processing metrics and performance monitoring

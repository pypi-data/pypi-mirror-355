import logging

class ModelInstance:
    """Manages a single model instance with loading, prediction, and lifecycle management."""
    
    def __init__(self, 
        load_model=None,
        predict=None,
        action_tracker=None,
        ):
        """Initialize the model instance with loading and prediction functions.

        Args:
            load_model: Function to load the model
            predict: Function to run predictions
            action_tracker: Tracker for monitoring actions
            
        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If model loading fails
        """
        if not load_model or not predict:
            raise ValueError("Both load_model and predict functions are required")
            
        self.action_tracker = action_tracker
        self.model = None
        self.predict_func = None
        
        try:
            logging.info("Loading model...")
            self.model = load_model(self.action_tracker)
            self.predict_func = self._create_prediction_wrapper(predict)
            logging.info("Model instance initialized successfully")
        except Exception as e:
            logging.error(
                "Failed to initialize model instance: %s",
                str(e),
                exc_info=True,
            )
            raise RuntimeError(f"Model initialization failed: {str(e)}") from e

    def _create_prediction_wrapper(self, predict_func):
        """Create a wrapper function that handles parameter passing to the prediction function.

        Args:
            predict_func: The prediction function to wrap

        Returns:
            A wrapper function that handles parameter passing safely
        """
        def wrapper(model, input1, input2=None, extra_params=None) -> dict:
            """Wrapper that safely calls the prediction function with proper parameter handling."""
            try:
                # Extract extra parameters and filter based on function signature
                extra_params = extra_params or {}
                param_names = predict_func.__code__.co_varnames[:predict_func.__code__.co_argcount]
                filtered_params = {k: v for k, v in extra_params.items() if k in param_names}
                
                # Build arguments list
                args = [model, input1]
                
                # Add optional second input if present
                if input2 is not None:
                    args.append(input2)
                
                return predict_func(*args, **filtered_params)
                
            except Exception as e:
                error_msg = f"Prediction function execution failed: {str(e)}"
                logging.error(error_msg, exc_info=True)
                raise RuntimeError(error_msg) from e

        return wrapper

    def inference(self, input1, input2=None, extra_params=None) -> tuple[dict, bool]:
        """Run inference on the provided input data.
        
        Args:
            input1: Primary input data
            input2: Secondary input data (optional)
            extra_params: Additional parameters for inference (optional)
            
        Returns:
            Tuple of (results, success_flag)
            
        Raises:
            ValueError: If input data is invalid
        """
        if input1 is None:
            raise ValueError("Input data cannot be None")
            
        try:
            logging.debug("Starting inference")
            
            # Run prediction
            results = self.predict_func(self.model, input1, input2, extra_params)
            
            # Update results through action tracker if available
            if self.action_tracker:
                results = self.action_tracker.update_prediction_results(results)
            
            logging.debug("Inference completed successfully")
            return results, True
            
        except Exception as e:
            logging.error(
                "Inference failed: %s",
                str(e),
                exc_info=True,
            )
            return None, False


class ModelManager:

    def __init__(self, 
        model_id: str,
        internal_server_type: str,
        internal_port: int,
        internal_host: str,
        load_model=None,
        predict=None,
        action_tracker=None,
        ):
        """Initialize the ModelManager with model loading and prediction functions

        Args:
            model_id: ID of the model
            internal_server_type: Type of internal server
            internal_port: Internal port number
            internal_host: Internal host address
            load_model: Function to load the model
            predict: Function to run predictions
            action_tracker: Tracker for monitoring actions
        """
        try:
            self.model_id = model_id
            self.internal_server_type = internal_server_type
            self.internal_port = internal_port
            self.internal_host = internal_host
            
            self.load_model = load_model
            self.predict = predict
            self.action_tracker = action_tracker
            
            # Initialize the model instance
            self.model_instance = ModelInstance(
                load_model=load_model,
                predict=predict,
                action_tracker=action_tracker
            )
            
        except Exception as e:
            logging.error(
                "Failed to initialize ModelManager: %s",
                str(e),
                exc_info=True,
            )
            raise

    async def inference(
        self, input1, input2=None, extra_params=None
    ):
        """Perform inference using the model instance.

        Args:
            input1: Primary input data
            input2: Secondary input data (optional)
            extra_params: Additional parameters for inference (optional)

        Returns:
            Inference result

        Raises:
            ValueError: If model instance is not set up
        """
        if not self.model_instance:
            raise ValueError("Model instance not initialized")

        # Run inference using the model instance
        results, success = self.model_instance.inference(input1, input2, extra_params)
        
        if not success:
            raise RuntimeError("Inference failed")
        
        return results
    

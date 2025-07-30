"""Module providing client_utils functionality."""

import json
import logging
from typing import (
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
import httpx


class ClientUtils:
    """Utility class for making inference requests to model servers."""

    def __init__(self, clients: List[Dict] = None):
        """Initialize HTTP clients."""
        self.http_client = httpx.Client(timeout=360, follow_redirects=True)
        self.async_client = httpx.AsyncClient(timeout=360, follow_redirects=True)
        self.clients: List[Dict] = clients if clients is not None else []
        self.client_number = 0
        logging.debug("Initialized ClientUtils")

    def refresh_instances_info(self, instances_info: List[Dict]) -> None:
        """Update clients with new instances info."""
        logging.debug("Updating clients with %d instances", len(instances_info))
        self.clients = [
            {
                "url": f"http://{instance['ip_address']}:{instance['port']}/inference",
                "instance_id": instance["instance_id"],
            }
            for instance in instances_info
        ]
        self.client_number = 0  # Reset client_number when refreshing instances
        logging.debug(
            "Successfully updated clients with %d instances", len(self.clients)
        )

    def _get_client(self):
        """Get client URL from instance info with round-robin load balancing."""
        if not self.clients:
            error_msg = "No clients available. Please refresh instances info or check deployment status."
            logging.error(error_msg)
            raise RuntimeError(error_msg)
            
        # Ensure client_number is within bounds
        if self.client_number >= len(self.clients):
            self.client_number = 0
            
        self.client = self.clients[self.client_number]
        self.client_number = (self.client_number + 1) % len(self.clients)
        
        logging.debug(
            "Selected client %s (%s) from %d available clients",
            self.client_number,
            self.client["url"],
            len(self.clients),
        )
        return self.client

    def _prepare_request_data(
        self,
        auth_key: str = None,
        input_path: Optional[str] = None,
        input_bytes: Optional[bytes] = None,
        input_url: Optional[str] = None,
        extra_params: Optional[Dict] = None,
        apply_post_processing: bool = False,
    ) -> Tuple[Dict, Dict]:
        """Prepare files and data for inference request.

        Args:
            auth_key: Authentication key
            input_path: Path to input file
            input_bytes: Input as bytes
            input_url: URL to fetch input from
            extra_params: Additional parameters to pass to model
            apply_post_processing: Whether to apply post-processing

        Returns:
            Tuple of (files dict, data dict)

        Raises:
            ValueError: If no input or auth key provided
        """
        if not any([input_path, input_bytes, input_url]):
            error_msg = "Must provide one of: input_path, input_bytes, or input_url"
            logging.error(error_msg)
            raise ValueError(error_msg)
        if not auth_key:
            raise ValueError("Must provide auth key")
        files = {}
        if input_path:
            files["input"] = open(input_path, "rb")
        elif input_bytes:
            files["input"] = input_bytes
        data = {"auth_key": auth_key, "apply_post_processing": str(apply_post_processing).lower()}
        if input_url:
            data["inputUrl"] = input_url
        if extra_params:
            data["extra_params"] = json.dumps(extra_params)
        return files, data

    def _handle_response(
        self,
        resp_json: Dict,
        is_async: bool = False,
    ) -> Union[Dict, str]:
        """Handle inference response.

        Args:
            resp_json: Response JSON from server
            is_async: Whether this was an async request

        Returns:
            Model prediction result

        Raises:
            Exception: If inference request failed
        """
        if "result" in resp_json:
            logging.debug(
                "Successfully got %sinference result",
                "async " if is_async else "",
            )
            return resp_json["result"]
        error_msg = "%sInference failed, response: %s" % (
            "Async " if is_async else "",
            resp_json,
        )
        logging.error(error_msg)
        raise Exception(error_msg)

    def inference(
        self,
        auth_key: str = None,
        input_path: Optional[str] = None,
        input_bytes: Optional[bytes] = None,
        input_url: Optional[str] = None,
        extra_params: Optional[Dict] = None,
        apply_post_processing: bool = False,
        max_retries: int = 2,
    ) -> Union[Dict, str]:
        """Make a synchronous inference request with retry logic.

        Args:
            auth_key: Authentication key
            input_path: Path to input file
            input_bytes: Input as bytes
            input_url: URL to fetch input from
            extra_params: Additional parameters to pass to model
            apply_post_processing: Whether to apply post-processing
            max_retries: Maximum number of retry attempts per client

        Returns:
            Model prediction result

        Raises:
            ValueError: If no input is provided
            httpx.HTTPError: If HTTP request fails
            Exception: If inference request fails
        """
        files = {}
        file_handle = None
        last_exception = None
        
        try:
            files, data = self._prepare_request_data(
                auth_key,
                input_path,
                input_bytes,
                input_url,
                extra_params,
                apply_post_processing,
            )
            if input_path:
                file_handle = files["input"]

            
            for attempt in range(max_retries + 1):
                client = self._get_client()
                try:
                    logging.debug(
                        "Making inference request to %s (attempt %d/%d)",
                        client["url"],
                        attempt + 1,
                        max_retries + 1
                    )
                    resp = self.http_client.post(
                        url=client["url"],
                        files=files,
                        data=data or None,
                    ).json()
                    return self._handle_response(resp)
                    
                except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as exc:
                    last_exception = exc
                    if attempt < max_retries:
                        logging.warning(
                            "Request to %s failed (attempt %d/%d): %s", 
                            client["url"], attempt + 1, max_retries + 1, str(exc)
                        )
                        continue
                    else:
                        logging.error(
                            "All retries exhausted for %s: %s", 
                            client["url"], str(exc)
                        )
                        break
                except Exception as exc:
                    last_exception = exc
                    logging.error("Inference failed on %s: %s", client["url"], str(exc))
                    break
            
            # If we get here, all clients failed
            error_msg = f"All inference attempts failed. Last error: {str(last_exception)}"
            logging.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as exc:
            if "All inference attempts failed" not in str(exc):
                error_msg = f"Inference setup failed: {str(exc)}"
                logging.error(error_msg)
                raise
            raise
        finally:
            if file_handle:
                file_handle.close()

    async def async_inference(
        self,
        auth_key: str = None,
        input_path: Optional[str] = None,
        input_bytes: Optional[bytes] = None,
        input_url: Optional[str] = None,
        extra_params: Optional[Dict] = None,
        apply_post_processing: bool = False,
        max_retries: int = 2,
    ) -> Union[Dict, str]:
        """Make an asynchronous inference request with retry logic.

        Args:
            auth_key: Authentication key
            input_path: Path to input file
            input_bytes: Input as bytes
            input_url: URL to fetch input from
            extra_params: Additional parameters to pass to model
            apply_post_processing: Whether to apply post-processing
            max_retries: Maximum number of retry attempts per client

        Returns:
            Model prediction result

        Raises:
            ValueError: If no input is provided
            httpx.HTTPError: If HTTP request fails
            Exception: If inference request fails
        """
        files = {}
        file_handle = None
        last_exception = None
        
        try:
            files, data = self._prepare_request_data(
                auth_key,
                input_path,
                input_bytes,
                input_url,
                extra_params,
                apply_post_processing,
            )
            if input_path:
                file_handle = files["input"]

            for attempt in range(max_retries + 1):
                client = self._get_client()
                try:
                    logging.debug(
                        "Making async inference request to %s (attempt %d/%d)",
                        client["url"],
                        attempt + 1,
                        max_retries + 1
                    )
                    resp = await self.async_client.post(
                        url=client["url"],
                        files=files,
                        data=data or None,
                    )
                    resp_json = resp.json()
                    return self._handle_response(resp_json, is_async=True)
                    
                except (httpx.HTTPError, httpx.ConnectError, httpx.TimeoutException) as exc:
                    last_exception = exc
                    if attempt < max_retries:
                        logging.warning(
                            "Async request to %s failed (attempt %d/%d): %s", 
                            client["url"], attempt + 1, max_retries + 1, str(exc)
                        )
                        continue
                    else:
                        logging.error(
                            "All async retries exhausted for %s: %s", 
                            client["url"], str(exc)
                        )
                        break
                except Exception as exc:
                    last_exception = exc
                    logging.error("Async inference failed on %s: %s", client["url"], str(exc))
                    break
            
            # If we get here, all clients failed
            error_msg = f"All async inference attempts failed. Last error: {str(last_exception)}"
            logging.error(error_msg)
            raise Exception(error_msg)
            
        except Exception as exc:
            if "All async inference attempts failed" not in str(exc):
                error_msg = f"Async inference setup failed: {str(exc)}"
                logging.error(error_msg)
                raise
            raise
        finally:
            if file_handle:
                file_handle.close()

    def close(self) -> None:
        """Close HTTP clients and clean up resources."""
        try:
            if hasattr(self, 'http_client'):
                self.http_client.close()
                logging.debug("Closed synchronous HTTP client")
        except Exception as exc:
            logging.warning("Error closing HTTP client: %s", str(exc))
            
        try:
            if hasattr(self, 'async_client'):
                # For async client, we need to handle it properly
                # Note: In practice, this should be called from an async context
                logging.debug("Async HTTP client cleanup scheduled")
        except Exception as exc:
            logging.warning("Error scheduling async client cleanup: %s", str(exc))
            
    async def aclose(self) -> None:
        """Asynchronously close HTTP clients and clean up resources."""
        try:
            if hasattr(self, 'http_client'):
                self.http_client.close()
                logging.debug("Closed synchronous HTTP client")
        except Exception as exc:
            logging.warning("Error closing HTTP client: %s", str(exc))
            
        try:
            if hasattr(self, 'async_client'):
                await self.async_client.aclose()
                logging.debug("Closed asynchronous HTTP client")
        except Exception as exc:
            logging.warning("Error closing async HTTP client: %s", str(exc))

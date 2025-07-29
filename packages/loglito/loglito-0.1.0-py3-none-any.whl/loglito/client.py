"""
Loglito Client Implementation

This module contains the main Loglito class for sending logs to the Loglito service.
"""

import json
import logging
import time
import threading
import queue
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


class LoglitoError(Exception):
    """Base exception for Loglito client errors."""

    pass


class LoglitoConnectionError(LoglitoError):
    """Raised when there's a connection error to the Loglito service."""

    pass


class LoglitoAuthenticationError(LoglitoError):
    """Raised when authentication fails (invalid API key)."""

    pass


class LoglitoServerError(LoglitoError):
    """Raised when the Loglito service returns a server error."""

    pass


class Loglito:
    """
    Loglito client for sending logs to the Loglito logging service.

    This client uses a background thread with buffering for optimal performance.
    Logs are automatically flushed every 2 seconds or when 100 logs accumulate.

    Args:
        api_key (str): Your Loglito API key
        base_url (str, optional): Base URL for the Loglito API.
                                 Defaults to 'https://loglito.io'
        timeout (float, optional): Request timeout in seconds. Defaults to 30.0
        retries (int, optional): Number of retry attempts for failed requests. Defaults to 3
        verify_ssl (bool, optional): Whether to verify SSL certificates. Defaults to True
        buffer_size (int, optional): Maximum number of logs to buffer before forcing flush. Defaults to 100
        flush_interval (float, optional): Time in seconds between automatic flushes. Defaults to 2.0
        immediate_mode (bool, optional): If True, logs are sent immediately without buffering. Defaults to False

    Example:
        >>> from loglito import Loglito
        >>> loglito = Loglito(api_key="your-api-key")
        >>> loglito.log("Hello world!")
        >>> loglito.log(message="User login", data={"username": "john", "ip": "1.2.3.4"})
        >>> loglito.log(level="error", message="Database connection failed", data={"error": "timeout"})
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://loglito.io",
        timeout: float = 30.0,
        retries: int = 3,
        verify_ssl: bool = True,
        buffer_size: int = 100,
        flush_interval: float = 2.0,
        immediate_mode: bool = False,
    ):
        if not api_key:
            raise ValueError("API key is required")

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.immediate_mode = immediate_mode

        # Create session with retry strategy
        self.session = requests.Session()

        # Set up retry strategy
        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=[
                "HEAD",
                "GET",
                "PUT",
                "DELETE",
                "OPTIONS",
                "TRACE",
                "POST",
            ],
            backoff_factor=1,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "api-key": self.api_key,
                "User-Agent": f"loglito-python/0.1.0",
            }
        )

        # Internal logger for debugging
        self._logger = logging.getLogger(__name__)

        # Initialize buffering system
        self._log_queue = queue.Queue()
        self._shutdown_event = threading.Event()
        self._buffer_lock = threading.Lock()
        self._current_buffer = []
        self._last_flush_time = time.time()

        # Start background thread for processing logs (unless in immediate mode)
        if not self.immediate_mode:
            self._worker_thread = threading.Thread(
                target=self._background_worker, daemon=True, name="loglito-worker"
            )
            self._worker_thread.start()
            self._logger.debug("Background worker thread started")
        else:
            self._worker_thread = None

    def _background_worker(self):
        """Background thread that processes logs from the queue and sends them."""
        self._logger.debug("Background worker started")

        while not self._shutdown_event.is_set():
            try:
                # Check if we should flush based on time
                current_time = time.time()
                time_since_last_flush = current_time - self._last_flush_time

                # Check if we should flush based on buffer size or time
                should_flush_time = time_since_last_flush >= self.flush_interval
                should_flush_size = len(self._current_buffer) >= self.buffer_size

                if should_flush_time or should_flush_size:
                    self._flush_buffer()

                # Process new logs from queue
                try:
                    # Wait for a log or timeout to check flush conditions
                    log_payload = self._log_queue.get(timeout=0.1)

                    with self._buffer_lock:
                        self._current_buffer.append(log_payload)

                    self._log_queue.task_done()

                    # Check if buffer is full after adding new log
                    if len(self._current_buffer) >= self.buffer_size:
                        self._flush_buffer()

                except queue.Empty:
                    # No new logs, continue to check flush conditions
                    continue

            except Exception as e:
                self._logger.error(f"Error in background worker: {e}")
                time.sleep(0.1)  # Prevent tight loop on errors

        # Flush remaining logs on shutdown
        self._flush_buffer()
        self._logger.debug("Background worker stopped")

    def _flush_buffer(self):
        """Flush the current buffer of logs."""
        with self._buffer_lock:
            if not self._current_buffer:
                return

            logs_to_send = self._current_buffer.copy()
            self._current_buffer.clear()
            self._last_flush_time = time.time()

        if logs_to_send:
            try:
                # Send as batch if multiple logs, otherwise send single log
                if len(logs_to_send) == 1:
                    self._send_log_direct(logs_to_send[0])
                else:
                    batch_payload = {
                        "logs": [{"log": log_data} for log_data in logs_to_send]
                    }
                    self._send_log_direct(batch_payload)

                self._logger.debug(f"Flushed {len(logs_to_send)} log(s)")

            except Exception as e:
                self._logger.error(f"Error flushing logs: {e}")
                # Could implement retry logic here

    def log(self, *args, **kwargs) -> bool:
        """
        Send a log entry to Loglito.

        In buffered mode (default), logs are queued and sent in batches for optimal performance.
        In immediate mode, logs are sent synchronously.

        This method supports multiple calling patterns:
        - loglito.log("Simple message")
        - loglito.log("info", "User subscribed", {"user_id": 123}, {"plan": "premium"})
        - loglito.log(message="Message", data={"key": "value"})
        - loglito.log(level="error", message="Error message", data={"error": "details"})
        - loglito.log(level="info", data={"event": "user_login", "user_id": 123})

        Args:
            *args: Positional arguments - can be (level, message, *data_dicts) or just (message,)
            **kwargs: Keyword arguments like message=, level=, data=, or any additional fields

        Returns:
            bool: True if the log was queued/sent successfully, False otherwise

        Raises:
            LoglitoAuthenticationError: If the API key is invalid (immediate mode only)
            LoglitoConnectionError: If there's a connection error (immediate mode only)
            LoglitoServerError: If the server returns an error (immediate mode only)
        """
        try:
            # Parse arguments
            parsed_level = kwargs.get("level")
            parsed_message = kwargs.get("message")
            data_from_kwargs = kwargs.get("data", {})
            data_dicts = []

            # Handle positional arguments
            if args:
                if (
                    len(args) == 1
                    and isinstance(args[0], str)
                    and not parsed_level
                    and not parsed_message
                ):
                    # Pattern: log("Simple message")
                    parsed_message = args[0]
                elif (
                    len(args) >= 2
                    and isinstance(args[0], str)
                    and isinstance(args[1], str)
                ):
                    # Pattern: log("level", "message", dict1, dict2, ...)
                    parsed_level = args[0]
                    parsed_message = args[1]
                    data_dicts = [arg for arg in args[2:] if isinstance(arg, dict)]
                elif len(args) >= 1:
                    # Fallback: treat remaining args as data dicts if first isn't a string
                    data_dicts = [arg for arg in args if isinstance(arg, dict)]

            # Build the log payload
            log_data = {}

            # Add timestamp
            log_data["__date"] = (
                datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            )

            # Add message
            if parsed_message is not None:
                log_data["__message"] = parsed_message

            # Add level
            if parsed_level is not None:
                log_data["__level"] = parsed_level

            # Add data from kwargs
            if data_from_kwargs:
                log_data.update(data_from_kwargs)

            # Add data from positional data dictionaries
            for data_dict in data_dicts:
                if isinstance(data_dict, dict):
                    log_data.update(data_dict)

            # Add other keyword arguments (excluding the special ones)
            for key, value in kwargs.items():
                if key not in ["level", "message", "data"]:
                    log_data[key] = value

            # Build the request payload according to the API specification
            # Always send as batch format with single log
            payload = {"logs": [{"log": log_data}]}

            # Send immediately or queue for background processing
            if self.immediate_mode:
                return self._send_log_direct(payload)
            else:
                # Queue the complete payload for background processing
                try:
                    self._log_queue.put_nowait(payload)
                    return True
                except queue.Full:
                    self._logger.error("Log queue is full, dropping log")
                    return False

        except LoglitoError:
            # Re-raise specific Loglito exceptions (immediate mode only)
            if self.immediate_mode:
                raise
            return False
        except Exception as e:
            # Log and return False for unexpected exceptions
            self._logger.error(f"Error sending log: {e}")
            return False

    def log_batch(self, logs: List[Dict[str, Any]]) -> bool:
        """
        Send multiple log entries.

        In buffered mode, logs are added to the queue individually.
        In immediate mode, logs are sent as a batch request.

        Args:
            logs (list): List of log dictionaries. Each log can have:
                        - "message": str
                        - "level": str
                        - "data": dict
                        - Any other key-value pairs

        Returns:
            bool: True if all logs were queued/sent successfully, False otherwise

        Example:
            >>> logs = [
            ...     {"message": "User login", "level": "info", "data": {"user_id": 123}},
            ...     {"message": "API call", "level": "debug", "data": {"endpoint": "/users"}},
            ... ]
            >>> loglito.log_batch(logs)
        """
        try:
            if self.immediate_mode:
                # Send as batch in immediate mode
                processed_logs = []

                for log_entry in logs:
                    log_data = {}

                    # Add timestamp
                    log_data["__date"] = (
                        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                    )

                    # Extract message and level
                    message = log_entry.get("message")
                    level = log_entry.get("level")
                    data = log_entry.get("data", {})

                    # Add message
                    if message is not None:
                        log_data["__message"] = message

                    # Add level
                    if level is not None:
                        log_data["__level"] = level

                    # Add data fields
                    log_data.update(data)

                    # Add all other fields to log_data
                    for key, value in log_entry.items():
                        if key not in ["message", "level", "data"]:
                            log_data[key] = value

                    # Build log item in new format
                    log_item = {"log": log_data}
                    processed_logs.append(log_item)

                payload = {"logs": processed_logs}
                return self._send_log_direct(payload)
            else:
                # Queue each log individually in buffered mode
                success_count = 0
                for log_entry in logs:
                    if self.log(**log_entry):
                        success_count += 1

                return success_count == len(logs)

        except LoglitoError:
            # Re-raise specific Loglito exceptions (immediate mode only)
            if self.immediate_mode:
                raise
            return False
        except Exception as e:
            # Log and return False for unexpected exceptions
            self._logger.error(f"Error sending batch logs: {e}")
            return False

    def _send_log_direct(self, payload: Dict[str, Any]) -> bool:
        """
        Internal method to send log payload directly to the API.

        Args:
            payload (dict): The log payload to send

        Returns:
            bool: True if successful, False otherwise

        Raises:
            LoglitoAuthenticationError: If the API key is invalid
            LoglitoConnectionError: If there's a connection error
            LoglitoServerError: If the server returns an error
        """
        url = f"{self.base_url}/api/log"

        try:
            print("sending:", payload)

            response = self.session.post(
                url,
                json=payload,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )

            if response.status_code == 403:
                raise LoglitoAuthenticationError(
                    "Authentication failed. Please check your API key."
                )
            elif response.status_code >= 500:
                raise LoglitoServerError(
                    f"Server error ({response.status_code}): {response.text}"
                )
            elif response.status_code >= 400:
                error_msg = f"Client error ({response.status_code}): {response.text}"
                if response.status_code == 401:
                    raise LoglitoAuthenticationError(error_msg)
                else:
                    raise LoglitoError(error_msg)

            response.raise_for_status()
            return True

        except requests.exceptions.ConnectionError as e:
            raise LoglitoConnectionError(f"Connection error: {e}")
        except requests.exceptions.Timeout as e:
            raise LoglitoConnectionError(f"Request timeout: {e}")
        except requests.exceptions.RequestException as e:
            raise LoglitoConnectionError(f"Request error: {e}")

    def flush(self, timeout: float = 5.0) -> bool:
        """
        Manually flush all queued logs.

        Args:
            timeout (float): Maximum time to wait for flush to complete

        Returns:
            bool: True if flush completed successfully
        """
        if self.immediate_mode:
            return True  # Nothing to flush in immediate mode

        try:
            # Force a flush
            self._flush_buffer()

            # Wait for queue to be empty
            start_time = time.time()
            while not self._log_queue.empty():
                if time.time() - start_time > timeout:
                    self._logger.warning("Flush timeout exceeded")
                    return False
                time.sleep(0.01)

            return True

        except Exception as e:
            self._logger.error(f"Error during flush: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Test the connection to Loglito by sending a test log.

        Returns:
            bool: True if the connection is successful, False otherwise
        """
        try:
            # Always send test connection immediately
            test_payload = {
                "logs": [
                    {
                        "log": {
                            "__date": datetime.now(timezone.utc)
                            .isoformat()
                            .replace("+00:00", "Z"),
                            "__message": "Test connection",
                            "__level": "info",
                            "__test": True,
                        }
                    }
                ]
            }

            return self._send_log_direct(test_payload)

        except LoglitoError:
            return False

    def info(
        self, message: str, data: Optional[Dict[str, Any]] = None, **kwargs
    ) -> bool:
        """
        Send an info level log entry.

        Args:
            message (str): The log message
            data (dict, optional): Additional data to include in the log
            **kwargs: Additional key-value pairs to include in the log

        Returns:
            bool: True if the log was sent/queued successfully, False otherwise

        Example:
            >>> loglito.info("User logged in", {"user_id": 123})
        """
        return self.log(level="info", message=message, data=data or {}, **kwargs)

    def debug(
        self, message: str, data: Optional[Dict[str, Any]] = None, **kwargs
    ) -> bool:
        """
        Send a debug level log entry.

        Args:
            message (str): The log message
            data (dict, optional): Additional data to include in the log
            **kwargs: Additional key-value pairs to include in the log

        Returns:
            bool: True if the log was sent/queued successfully, False otherwise

        Example:
            >>> loglito.debug("API response", {"status": 200, "endpoint": "/users"})
        """
        return self.log(level="debug", message=message, data=data or {}, **kwargs)

    def warning(
        self, message: str, data: Optional[Dict[str, Any]] = None, **kwargs
    ) -> bool:
        """
        Send a warning level log entry.

        Args:
            message (str): The log message
            data (dict, optional): Additional data to include in the log
            **kwargs: Additional key-value pairs to include in the log

        Returns:
            bool: True if the log was sent/queued successfully, False otherwise

        Example:
            >>> loglito.warning("Rate limit approaching", {"current_usage": 85, "limit": 100})
        """
        return self.log(level="warning", message=message, data=data or {}, **kwargs)

    def error(
        self, message: str, data: Optional[Dict[str, Any]] = None, **kwargs
    ) -> bool:
        """
        Send an error level log entry.

        Args:
            message (str): The log message
            data (dict, optional): Additional data to include in the log
            **kwargs: Additional key-value pairs to include in the log

        Returns:
            bool: True if the log was sent/queued successfully, False otherwise

        Example:
            >>> loglito.error("Database connection failed", {"error": "timeout", "retries": 3})
        """
        return self.log(level="error", message=message, data=data or {}, **kwargs)

    def close(self) -> None:
        """Close the client and flush any remaining logs."""
        if (
            not self.immediate_mode
            and self._worker_thread
            and self._worker_thread.is_alive()
        ):
            # Signal shutdown and wait for worker to finish
            self._shutdown_event.set()
            self._worker_thread.join(timeout=5.0)

            if self._worker_thread.is_alive():
                self._logger.warning("Worker thread did not shut down gracefully")

        if self.session:
            self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - flush and close."""
        if not self.immediate_mode:
            self.flush()
        self.close()

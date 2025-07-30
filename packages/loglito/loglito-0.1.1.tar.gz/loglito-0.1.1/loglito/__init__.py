"""
Loglito Python Client Library

A simple and efficient Python client for sending logs to Loglito logging service.

Usage:
    from loglito import Loglito

    loglito = Loglito(api_key="your-api-key")
    loglito.log("Hello world!")
    loglito.log(message="Hello user", data={"username": "john"})
    loglito.log(level="warning", message="login required", data={"username": "john"})
"""

from .client import Loglito

__version__ = "0.1.0"
__all__ = ["Loglito"]

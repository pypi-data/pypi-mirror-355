"""Plugin for httpbin.org API testing.

httpbin.org is a simple HTTP Request & Response Service.
Perfect for testing HTTP libraries and tools.
"""

import json
import requests
from typing import Dict, Any, Optional, List


def safe_execute(func):
    """Decorator for safe execution."""
    def wrapper(*args, **kwargs):
        try:
            return {"success": True, "data": func(*args, **kwargs)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    return wrapper


@safe_execute
def httpbin_get(endpoint: str = "/get", **params) -> Dict[str, Any]:
    """Make a GET request to httpbin.
    
    Args:
        endpoint: The endpoint path (e.g., "/get", "/status/200")
        **params: Query parameters to include
        
    Returns:
        Response data from httpbin
    """
    url = f"https://httpbin.org{endpoint}"
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    try:
        return response.json()
    except:
        return {"text": response.text, "status_code": response.status_code}


@safe_execute
def httpbin_post(endpoint: str = "/post", json_data: Optional[Dict] = None, form_data: Optional[Dict] = None) -> Dict[str, Any]:
    """Make a POST request to httpbin.
    
    Args:
        endpoint: The endpoint path (e.g., "/post", "/anything")
        json_data: JSON data to send in request body
        form_data: Form data to send (if not using JSON)
        
    Returns:
        Response data from httpbin showing what was sent
    """
    url = f"https://httpbin.org{endpoint}"
    
    if json_data:
        response = requests.post(url, json=json_data)
    elif form_data:
        response = requests.post(url, data=form_data)
    else:
        response = requests.post(url)
    
    response.raise_for_status()
    return response.json()


@safe_execute
def httpbin_test_auth(username: str = "testuser", password: str = "testpass") -> Dict[str, Any]:
    """Test basic authentication.
    
    Args:
        username: Username for basic auth
        password: Password for basic auth
        
    Returns:
        Response showing if auth was successful
    """
    url = f"https://httpbin.org/basic-auth/{username}/{password}"
    response = requests.get(url, auth=(username, password))
    
    if response.status_code == 200:
        return response.json()
    else:
        return {
            "authenticated": False,
            "status_code": response.status_code,
            "reason": response.reason
        }


@safe_execute
def httpbin_test_status(code: int = 200) -> Dict[str, Any]:
    """Test a specific HTTP status code.
    
    Args:
        code: HTTP status code to test (e.g., 200, 404, 500)
        
    Returns:
        Response with the requested status code
    """
    url = f"https://httpbin.org/status/{code}"
    response = requests.get(url)
    
    return {
        "status_code": response.status_code,
        "reason": response.reason,
        "ok": response.ok,
        "url": response.url
    }


def get_httpbin_tools() -> Dict[str, Dict[str, Any]]:
    """Get all httpbin tools for the plugin system.
    
    Returns:
        Dictionary of tool configurations
    """
    return {
        "httpbin_get": {
            "description": "Make a GET request to httpbin.org for testing",
            "schema": {
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "The endpoint path (e.g., '/get', '/headers')",
                        "default": "/get"
                    },
                    "params": {
                        "type": "object",
                        "description": "Query parameters to include",
                        "additionalProperties": {"type": "string"}
                    }
                }
            },
            "func": httpbin_get
        },
        "httpbin_post": {
            "description": "Make a POST request to httpbin.org with JSON or form data",
            "schema": {
                "type": "object",
                "properties": {
                    "endpoint": {
                        "type": "string",
                        "description": "The endpoint path (e.g., '/post', '/anything')",
                        "default": "/post"
                    },
                    "json_data": {
                        "type": "object",
                        "description": "JSON data to send in request body",
                        "additionalProperties": True
                    },
                    "form_data": {
                        "type": "object",
                        "description": "Form data to send (if not using JSON)",
                        "additionalProperties": {"type": "string"}
                    }
                }
            },
            "func": httpbin_post
        },
        "httpbin_test_auth": {
            "description": "Test basic authentication with httpbin.org",
            "schema": {
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "Username for basic auth",
                        "default": "testuser"
                    },
                    "password": {
                        "type": "string",
                        "description": "Password for basic auth",
                        "default": "testpass"
                    }
                }
            },
            "func": httpbin_test_auth
        },
        "httpbin_test_status": {
            "description": "Test a specific HTTP status code response",
            "schema": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "integer",
                        "description": "HTTP status code to test (e.g., 200, 404, 500)",
                        "default": 200,
                        "minimum": 100,
                        "maximum": 599
                    }
                }
            },
            "func": httpbin_test_status
        }
    }
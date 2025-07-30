"""
D5M AI Utilities Module

Common utilities shared across D5M AI components.
"""

import os


def get_remote_backend_url(service_type: str, use_ssl: bool = None) -> str:
    """
    Construct remote backend URL for different services from a single hostname.
    
    Args:
        service_type: One of 'agent', 'edit', 'chat'
        use_ssl: Whether to use SSL/TLS. If None, auto-detects based on hostname
        
    Returns:
        Complete URL for the specified service
    """
    # Get hostname from environment, default to localhost for development
    host = os.environ.get("D5M_REMOTE_HOST", "localhost:8891")
    
    # Auto-detect SSL based on hostname patterns
    if use_ssl is None:
        use_ssl = not (host.startswith("localhost") or host.startswith("127.0.0.1") or ":" in host.split(".")[0])
    
    # Determine protocol and construct base URL
    if service_type == "chat":
        protocol = "https" if use_ssl else "http"
        base_url = f"{protocol}://{host}"
        return f"{base_url}/chat"
    else:
        protocol = "wss" if use_ssl else "ws"
        base_url = f"{protocol}://{host}"
        return f"{base_url}/{service_type}"


def get_legacy_remote_backend_url(service_type: str) -> str:
    """
    Get remote backend URL using legacy environment variables for backward compatibility.
    
    Args:
        service_type: One of 'agent', 'edit', 'chat'
        
    Returns:
        URL from legacy environment variable or None if not set
    """
    legacy_env_vars = {
        "agent": "D5M_REMOTE_BACKEND_URL",
        "edit": "D5M_EDIT_REMOTE_BACKEND_URL", 
        "chat": "D5M_CHAT_REMOTE_BACKEND_URL"
    }
    
    env_var = legacy_env_vars.get(service_type)
    if env_var:
        return os.environ.get(env_var)
    return None


def build_remote_backend_url(service_type: str) -> str:
    """
    Build remote backend URL with fallback to legacy environment variables.
    
    This function provides a migration path from multiple service-specific 
    environment variables to a single D5M_REMOTE_HOST variable.
    
    Args:
        service_type: One of 'agent', 'edit', 'chat'
        
    Returns:
        Complete URL for the specified service
    """
    # First, try legacy environment variables for backward compatibility
    legacy_url = get_legacy_remote_backend_url(service_type)
    if legacy_url:
        return legacy_url
    
    # Otherwise, construct from D5M_REMOTE_HOST
    return get_remote_backend_url(service_type) 
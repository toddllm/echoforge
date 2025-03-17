#!/usr/bin/env python
"""
EchoForge Runner Script

This script provides a command-line interface to start the EchoForge server.
"""

import argparse
import logging
import os
import socket
import sys
from app.core import config
import uvicorn


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("echoforge.runner")


def is_port_available(host, port):
    """Check if a port is available on the host."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except socket.error:
            return False


def find_available_port(preferred_port, host=config.DEFAULT_HOST, max_attempts=config.MAX_PORT_ATTEMPTS):
    """
    Find an available port starting from the preferred port.
    
    Args:
        preferred_port: The port to try first
        host: The host to bind to
        max_attempts: Maximum number of ports to try
        
    Returns:
        An available port number or None if no port is available
    """
    # First try our unique EchoForge port
    if is_port_available(host, preferred_port):
        return preferred_port
        
    logger.warning(f"Preferred port {preferred_port} is already in use")
    
    # Try sequential ports starting from the preferred one
    current_port = preferred_port + 1
    for _ in range(max_attempts):
        if is_port_available(host, current_port):
            logger.info(f"Found available port: {current_port}")
            return current_port
        current_port += 1
    
    # If we've tried all ports and none are available, return None
    logger.error(f"Could not find available port after trying {max_attempts} ports")
    return None


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Start the EchoForge server")
    
    parser.add_argument(
        "--host", 
        default=None,
        help=f"Host to bind the server to (default: {config.DEFAULT_HOST} or {config.PUBLIC_HOST} if --public)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=config.DEFAULT_PORT,
        help=f"Port to bind the server to (default: {config.DEFAULT_PORT})"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true",
        help="Enable auto-reload on code changes (for development)"
    )
    
    parser.add_argument(
        "--force-port", 
        action="store_true",
        help="Fail if the specified port is not available, instead of trying alternatives"
    )
    
    parser.add_argument(
        "--public", 
        action="store_true",
        help=f"Serve on {config.PUBLIC_HOST} to make the app publicly accessible"
    )
    
    # Direct CSM arguments
    parser.add_argument(
        "--direct-csm", 
        action="store_true",
        help="Enable Direct CSM implementation (default: enabled)"
    )
    
    parser.add_argument(
        "--no-direct-csm", 
        action="store_false",
        dest="direct_csm",
        help="Disable Direct CSM implementation"
    )
    
    parser.add_argument(
        "--direct-csm-path",
        help=f"Path to Direct CSM implementation (default: {config.DIRECT_CSM_PATH})"
    )
    
    # Auth arguments - support both styles for compatibility
    parser.add_argument(
        "--auth", 
        action="store_true",
        help="Enable authentication (required for public serving by default)"
    )
    
    # Support the new auth parameter format used by the test scripts
    parser.add_argument(
        "--auth-user",
        help="Set custom username for authentication (enables auth)"
    )
    
    parser.add_argument(
        "--auth-pass",
        help="Set custom password for authentication (enables auth)"
    )
    
    # Support the old auth parameter format
    parser.add_argument(
        "--username",
        help="Set custom username for authentication (requires --auth)"
    )
    
    parser.add_argument(
        "--password",
        help="Set custom password for authentication (requires --auth)"
    )
    
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Disable authentication even when serving publicly (NOT RECOMMENDED)"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the runner script."""
    args = parse_arguments()
    
    # Handle command-line options vs environment variables
    
    # Public serving option
    public_serving = args.public or config.ALLOW_PUBLIC_SERVING
    
    # Authentication settings - handle both auth parameter styles
    enable_auth = args.auth or config.ENABLE_AUTH or args.auth_user is not None or args.auth_pass is not None
    
    # If authentication is explicitly enabled, use provided credentials or defaults
    if args.username or args.auth_user:
        os.environ["AUTH_USERNAME"] = args.auth_user or args.username
    
    if args.password or args.auth_pass:
        os.environ["AUTH_PASSWORD"] = args.auth_pass or args.password
    
    # Direct CSM settings
    if hasattr(args, 'direct_csm'):
        os.environ["USE_DIRECT_CSM"] = str(args.direct_csm).lower()
        logger.info(f"Direct CSM is {'enabled' if args.direct_csm else 'disabled'}")
    
    if args.direct_csm_path:
        os.environ["DIRECT_CSM_PATH"] = args.direct_csm_path
        logger.info(f"Using Direct CSM path: {args.direct_csm_path}")
    
    # Set appropriate environment variables based on arguments
    if public_serving:
        os.environ["ALLOW_PUBLIC_SERVING"] = "true"
        
        # Default to requiring auth for public serving, unless explicitly disabled
        if args.no_auth:
            logger.warning("SECURITY RISK: Authentication disabled for public serving")
            os.environ["AUTH_REQUIRED_FOR_PUBLIC"] = "false"
        else:
            os.environ["AUTH_REQUIRED_FOR_PUBLIC"] = "true"
            enable_auth = True  # Force auth for public serving
    
    if enable_auth:
        os.environ["ENABLE_AUTH"] = "true"
        
        # Print auth status
        username = os.environ.get("AUTH_USERNAME", config.AUTH_USERNAME)
        password = os.environ.get("AUTH_PASSWORD", config.AUTH_PASSWORD)
        
        if username == "echoforge" and password == "changeme123":
            logger.warning("SECURITY RISK: Using default credentials. Please set custom username and password.")
    
    # Determine host to use
    if args.host:
        host = args.host
    else:
        host = config.PUBLIC_HOST if public_serving else config.DEFAULT_HOST
    
    # Check if the port is available or find an alternative
    if args.force_port:
        if not is_port_available(host, args.port):
            logger.error(f"Port {args.port} is not available and --force-port is set")
            sys.exit(1)
        port = args.port
    else:
        port = find_available_port(args.port, host)
        if port is None:
            logger.error("Could not find an available port to start EchoForge")
            sys.exit(1)
    
    # Print server information
    access_info = f"http://{host}:{port}"
    if host == "0.0.0.0":
        access_info += " (available on all network interfaces)"
    logger.info(f"Starting EchoForge on {access_info}")
    
    if public_serving:
        logger.info("Server is publicly accessible")
        if enable_auth:
            logger.info(f"Authentication required with username: {username}")
        else:
            logger.warning("SECURITY RISK: Public server running without authentication")
    
    if port != args.port:
        logger.info(f"Note: Using port {port} instead of requested port {args.port} (already in use)")
    
    # Start the server
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=args.reload
    )


if __name__ == "__main__":
    main() 
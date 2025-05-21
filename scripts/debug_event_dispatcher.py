"""
debug_event_dispatcher.py - Script to test the custom event dispatching service with more detailed logging

This script tests the EventDispatcher service with more detailed output and simplified logic.

Usage:
    python scripts/debug_event_dispatcher.py

Dependencies:
    requests (should already be installed)
"""
import time
import json
import requests
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USER_ID = 1  # Use the user ID we created
TEST_MESSAGE = "Hello"  # Simple message to minimize potential issues


def test_health_endpoint():
    """Test if the server is running by checking health endpoint"""
    try:
        logger.info(f"Checking if server is running at {BASE_URL}/health")
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        logger.info(f"Server is running. Status code: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        return True
    except Exception as e:
        logger.error(f"Server is not running: {str(e)}")
        return False


def test_chat_endpoint_simple():
    """Test the chat endpoint with reduced complexity"""
    logger.info("=== Testing /events/chat endpoint with simplified test ===")
    
    # Build the URL
    url = f"{BASE_URL}/events/chat?user_id={TEST_USER_ID}&message={TEST_MESSAGE}"
    
    logger.info(f"POST Request to {url}")
    
    try:
        # Send the POST request with stream=True to get streaming response
        response = requests.post(url, stream=True, timeout=10)
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {dict(response.headers)}")
        
        if response.status_code != 200:
            logger.error(f"Error: {response.text}")
            return
        
        # Process the streaming response
        buffer = ""
        event_count = 0
        
        logger.info("Reading events from stream:")
        logger.info("=" * 60)
        
        # Read raw content
        for chunk in response.iter_content(chunk_size=1):
            if not chunk:
                continue
                
            # Convert the chunk to a string
            try:
                char = chunk.decode('utf-8')
                logger.debug(f"Received byte: {ord(char)} => '{char}'")
                buffer += char
                
                # When we see a double newline, we have a complete event
                if buffer.endswith('\n\n'):
                    logger.info(f"COMPLETE EVENT: {buffer.strip()}")
                    event_count += 1
                    buffer = ""
            except Exception as e:
                logger.error(f"Error processing chunk: {str(e)}")
        
        logger.info(f"Processed {event_count} events")
        logger.info(f"Remaining buffer: {buffer}")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")


def main():
    """Main function to run the tests"""
    if not test_health_endpoint():
        logger.error("Please start the server first: python scripts/run_server.py")
        sys.exit(1)
    
    logger.info(f"Using test user ID: {TEST_USER_ID}")
    logger.info("Make sure test user exists by running: python scripts/create_test_user_direct.py")
    
    # Run the simplified test
    test_chat_endpoint_simple()
    
    logger.info("Test complete")


if __name__ == "__main__":
    main()
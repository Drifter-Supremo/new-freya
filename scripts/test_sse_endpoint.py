"""
test_sse_endpoint.py - Script to test the SSE endpoint functionality

This script sends a test message to Freya using the /events/chat endpoint.

Usage:
    python scripts/test_sse_endpoint.py

Dependencies:
    requests (should already be installed)
"""
import time
import json
import requests
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = 1  # Use the user ID we created


def send_test_message():
    """Send a test message and process the streaming response"""
    # Prepare the message
    message = "Hello, Freya! Tell me about yourself."
    logger.info(f"Sending test message: '{message}'")
    
    # Build the URL
    url = f"{BASE_URL}/events/chat?user_id={TEST_USER_ID}&message={message}"
    
    # Send the POST request with stream=True to get streaming response
    logger.info(f"POST Request to {url}")
    
    try:
        # Set a longer timeout for the request to handle SSE streaming
        response = requests.post(url, stream=True, timeout=60)
        
        logger.info(f"Response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Error: {response.text}")
            return
        
        # Process the streaming response
        buffer = ""
        event_count = 0
        
        logger.info("Reading events from stream:")
        logger.info("=" * 60)
        
        # Read and process events from the stream
        for chunk in response.iter_content(chunk_size=1):
            if not chunk:
                continue
                
            # Convert the chunk to a string
            char = chunk.decode('utf-8')
            buffer += char
            
            # When we see a double newline, we have a complete event
            if buffer.endswith('\n\n'):
                # Split into lines
                lines = buffer.strip().split('\n')
                event_type = None
                event_data = None
                
                # Extract event type and data
                for line in lines:
                    if line.startswith('event:'):
                        event_type = line[6:].strip()
                    elif line.startswith('data:'):
                        event_data = line[5:].strip()
                
                # Log the event
                if event_type and event_data:
                    event_count += 1
                    logger.info(f"EVENT #{event_count}: {event_type}")
                    
                    try:
                        # Try to parse as JSON
                        data = json.loads(event_data)
                        if event_type == 'freya:reply' and 'message' in data:
                            logger.info(f"FREYA SAYS: {data['message']}")
                        else:
                            logger.info(f"DATA: {json.dumps(data, indent=2)}")
                    except:
                        logger.info(f"RAW DATA: {event_data}")
                    
                    logger.info("-" * 60)
                
                # Reset the buffer
                buffer = ""
                
                # Stop after receiving a sufficient number of events
                if event_count >= 20:  # Set a reasonable limit
                    logger.info("Reached maximum number of events to process")
                    break
        
        logger.info(f"Processed {event_count} events")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")


def main():
    """Main function to run the test"""
    try:
        # Check if server is running
        logger.info(f"Checking if server is running at {BASE_URL}/health")
        response = requests.get(f"{BASE_URL}/health")
        logger.info(f"Server is running. Status code: {response.status_code}")
    except Exception as e:
        logger.error(f"Error: Server is not running: {str(e)}")
        logger.error("Please start the server first: python scripts/run_server.py")
        sys.exit(1)
    
    logger.info(f"Using test user ID: {TEST_USER_ID}")
    logger.info("Make sure test user exists by running: python scripts/create_test_user_direct.py")
    
    # Send the test message and process the response
    send_test_message()
    
    logger.info("Test complete")


if __name__ == "__main__":
    main()

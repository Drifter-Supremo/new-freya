"""
test_sse_raw.py - Script to test the SSE endpoint with raw event handling
"""
import time
import json
import requests
import logging
import sys
import urllib.parse

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
    encoded_message = urllib.parse.quote(message)
    logger.info(f"Sending test message: '{message}'")
    
    # Build the URL
    url = f"{BASE_URL}/events/chat?user_id={TEST_USER_ID}&message={encoded_message}"
    
    # Send the POST request with stream=True to get streaming response
    logger.info(f"POST Request to {url}")
    
    try:
        # Set headers for SSE
        headers = {
            'Accept': 'text/event-stream',
            'Cache-Control': 'no-cache'
        }
        
        # Set a longer timeout for the request to handle SSE streaming
        response = requests.post(url, stream=True, headers=headers, timeout=60)
        
        logger.info(f"Response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Error: {response.text}")
            return
        
        # Process the streaming response
        buffer = ""
        event_count = 0
        
        logger.info("Reading events from stream:")
        logger.info("=" * 60)
        
        # Directly read the raw content from the response to debug
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                logger.info(f"RAW LINE: {decoded_line}")
                
                # When we see an event line, extract it
                if decoded_line.startswith('event:'):
                    event_type = decoded_line[6:].strip()
                    logger.info(f"EVENT TYPE: {event_type}")
                
                # When we see a data line, extract it
                if decoded_line.startswith('data:'):
                    data = decoded_line[5:].strip()
                    logger.info(f"DATA: {data}")
                    
                    try:
                        # Try to parse as JSON
                        json_data = json.loads(data)
                        if 'message' in json_data:
                            logger.info(f"MESSAGE: {json_data['message']}")
                    except json.JSONDecodeError:
                        pass
                    
                    event_count += 1
            
            # Set a reasonable limit
            if event_count >= 50:
                logger.info("Reached maximum number of events to process")
                break
        
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
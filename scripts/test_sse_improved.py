"""
test_sse_improved.py - Script to test the SSE endpoint functionality using sseclient
"""
import time
import json
import requests
import logging
import sys
import sseclient
import urllib.parse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_ID = 1  # Use the user ID we created


def send_test_message():
    """Send a test message and process the streaming response using sseclient"""
    # Prepare the message
    message = "Hello, Freya! Tell me about yourself."
    encoded_message = urllib.parse.quote(message)
    logger.info(f"Sending test message: '{message}'")
    
    # Build the URL
    url = f"{BASE_URL}/events/chat?user_id={TEST_USER_ID}&message={encoded_message}"
    
    logger.info(f"POST Request to {url}")
    
    try:
        # Use sseclient for better SSE handling
        response = requests.post(url, stream=True, timeout=120)
        
        logger.info(f"Response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Error: {response.text}")
            return
        
        # Create SSE client from the response
        client = sseclient.SSEClient(response)
        event_count = 0
        
        logger.info("Reading events from stream:")
        logger.info("=" * 60)
        
        # Process events
        for event in client.events():
            event_count += 1
            logger.info(f"EVENT #{event_count}: {event.event}")
            
            try:
                # Try to parse the data as JSON
                data = json.loads(event.data)
                
                if event.event == 'freya:reply' and 'message' in data:
                    logger.info(f"FREYA SAYS: {data['message']}")
                else:
                    logger.info(f"DATA: {json.dumps(data, indent=2)}")
            except:
                logger.info(f"RAW DATA: {event.data}")
            
            logger.info("-" * 60)
            
            # Set a reasonable limit to prevent infinite loops
            if event_count >= 20:
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
        logger.error("Please start the server first with the command:")
        logger.error("source venv/bin/activate && uvicorn app.main:app --reload")
        sys.exit(1)
    
    logger.info(f"Using test user ID: {TEST_USER_ID}")
    
    # Send the test message and process the response
    send_test_message()
    
    logger.info("Test complete")


if __name__ == "__main__":
    main()
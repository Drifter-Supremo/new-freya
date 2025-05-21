"""
test_event_dispatcher.py - Script to test the custom event dispatching service

This script tests the new EventDispatcher service with both /chat and /legacy endpoints.

Usage:
    python scripts/test_event_dispatcher.py

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
BASE_URL = "http://127.0.0.1:8000"
TEST_USER_ID = 1  # Use the user ID we created
TEST_MESSAGE = "Hello Freya, tell me about a memory from Saturn. Do you have medical knowledge?"


def test_chat_endpoint():
    """Test the enhanced /chat endpoint with the new EventDispatcher"""
    logger.info("=== Testing /chat endpoint with EventDispatcher ===")
    
    # Build the URL - note we're using the normal chat endpoint which now uses EventDispatcher
    url = f"{BASE_URL}/events/chat?user_id={TEST_USER_ID}&message={TEST_MESSAGE}"
    
    logger.info(f"POST Request to {url}")
    
    try:
        # Send the POST request with stream=True to get streaming response
        response = requests.post(url, stream=True, timeout=60)
        
        logger.info(f"Response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Error: {response.text}")
            return
        
        # Process the streaming response
        buffer = ""
        event_count = 0
        response_chunks = []
        
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
                            response_chunks.append(data['message'])
                        else:
                            logger.info(f"DATA: {json.dumps(data, indent=2)}")
                    except:
                        logger.info(f"RAW DATA: {event_data}")
                    
                    logger.info("-" * 60)
                
                # Reset the buffer
                buffer = ""
                
                # Stop after receiving a sufficient number of events or a timeout
                if event_count >= 30:  # Set a reasonable limit
                    logger.info("Reached maximum number of events to process")
                    break
        
        logger.info(f"Processed {event_count} events")
        
        # Display the full response
        if response_chunks:
            full_response = "".join(response_chunks)
            logger.info(f"FULL RESPONSE: {full_response}")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")


def test_legacy_endpoint():
    """Test the new /legacy endpoint that simulates the legacy frontend behavior"""
    logger.info("=== Testing /legacy endpoint with EventDispatcher ===")
    
    # Build the URL
    url = f"{BASE_URL}/events/legacy?user_id={TEST_USER_ID}&message={TEST_MESSAGE}"
    
    logger.info(f"POST Request to {url}")
    
    try:
        # Send the POST request with stream=True to get streaming response
        response = requests.post(url, stream=True, timeout=60)
        
        logger.info(f"Response status: {response.status_code}")
        if response.status_code != 200:
            logger.error(f"Error: {response.text}")
            return
        
        # Process the streaming response
        buffer = ""
        event_count = 0
        stages = []
        full_response = ""
        
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
                        
                        # Track the event sequence
                        if event_type == 'freya:listening':
                            stages.append('listening')
                            logger.info("STAGE: Freya is listening")
                        elif event_type == 'freya:thinking':
                            stages.append('thinking')
                            logger.info("STAGE: Freya is thinking")
                        elif event_type == 'freya:reply' and 'message' in data:
                            stages.append('reply')
                            logger.info(f"STAGE: Freya replied with: {data['message']}")
                            full_response = data['message']
                        else:
                            logger.info(f"DATA: {json.dumps(data, indent=2)}")
                    except:
                        logger.info(f"RAW DATA: {event_data}")
                    
                    logger.info("-" * 60)
                
                # Reset the buffer
                buffer = ""
                
                # Stop after receiving a sufficient number of events or a timeout
                if event_count >= 10:  # Set a reasonable limit for the non-streaming case
                    logger.info("Reached maximum number of events to process")
                    break
        
        logger.info(f"Processed {event_count} events")
        
        # Verify that we got the correct sequence of events
        if stages == ['listening', 'thinking', 'reply']:
            logger.info("SUCCESS: Received correct event sequence (listening -> thinking -> reply)")
        else:
            logger.error(f"ERROR: Unexpected event sequence: {stages}")
        
        # Display the full response
        if full_response:
            logger.info(f"FULL RESPONSE: {full_response}")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")


def main():
    """Main function to run the tests"""
    # Try different URLs in case the server is running on a different address
    urls_to_try = [
        "http://127.0.0.1:8000/health",
        "http://localhost:8000/health",
        "http://0.0.0.0:8000/health"
    ]
    
    server_running = False
    for url in urls_to_try:
        try:
            logger.info(f"Checking if server is running at {url}")
            response = requests.get(url, timeout=2)
            logger.info(f"Server is running at {url}. Status code: {response.status_code}")
            # Update the BASE_URL to the working URL
            global BASE_URL
            BASE_URL = url.rsplit("/", 1)[0]  # Remove "/health" from the URL
            server_running = True
            break
        except Exception as e:
            logger.warning(f"Server not available at {url}: {str(e)}")
    
    if not server_running:
        logger.error("Server is not running on any of the tried addresses.")
        logger.error("Please start the server first: python scripts/run_server.py")
        sys.exit(1)
    
    logger.info(f"Using test user ID: {TEST_USER_ID}")
    logger.info("Make sure test user exists by running: python scripts/create_test_user_direct.py")
    
    # Run tests
    test_chat_endpoint()
    
    # Wait a moment before the next test
    time.sleep(2)
    
    test_legacy_endpoint()
    
    logger.info("All tests complete")


if __name__ == "__main__":
    main()
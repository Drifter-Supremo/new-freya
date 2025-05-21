"""
test_events.py - Simple test for event dispatcher and routes

This script directly tests our event dispatcher functionality without requiring
the full server infrastructure.
"""
import asyncio
import json
from app.services.event_dispatcher import EventDispatcher

async def test_event_dispatcher():
    """Test the EventDispatcher class methods"""
    print("\n=== Testing EventDispatcher ===")
    
    # Create a test queue
    queue = asyncio.Queue()
    
    # Create the dispatcher
    dispatcher = EventDispatcher()
    
    # Test dispatching a sequence of events
    await dispatcher.dispatch_listening_event(queue)
    await dispatcher.dispatch_thinking_event(queue)
    await dispatcher.dispatch_reply_event(queue, "This is a test response")
    
    # Check the queue contents
    print("\nEvents in queue:")
    while not queue.empty():
        event = await queue.get()
        # Parse the event
        lines = event.strip().split('\n')
        event_type = None
        event_data = None
        
        # Extract event type and data
        for line in lines:
            if line.startswith('event:'):
                event_type = line[6:].strip()
            elif line.startswith('data:'):
                event_data = line[5:].strip()
        
        if event_type and event_data:
            print(f"EVENT: {event_type}")
            data = json.loads(event_data)
            print(f"DATA: {json.dumps(data, indent=2)}")
            print("-" * 40)
    
    print("\nTest completed successfully!")

async def test_chat_sequence():
    """Test chat sequence dispatcher"""
    print("\n=== Testing Chat Sequence ===")
    
    # Create a test queue
    queue = asyncio.Queue()
    
    # Create the dispatcher
    dispatcher = EventDispatcher()
    
    # Define a simple async processor function
    async def process_message(msg):
        await asyncio.sleep(0.5)  # Simulate processing
        return f"Response to: {msg}"
    
    # Test the chat sequence
    result = await dispatcher.dispatch_chat_sequence(
        client_queue=queue,
        message_processor=process_message,
        user_message="Hello, test!",
        thinking_delay=0.2
    )
    
    print(f"Result: {result}")
    
    # Check the queue contents
    print("\nEvents in queue:")
    while not queue.empty():
        event = await queue.get()
        # Parse the event
        lines = event.strip().split('\n')
        event_type = None
        event_data = None
        
        # Extract event type and data
        for line in lines:
            if line.startswith('event:'):
                event_type = line[6:].strip()
            elif line.startswith('data:'):
                event_data = line[5:].strip()
        
        if event_type and event_data:
            print(f"EVENT: {event_type}")
            data = json.loads(event_data)
            print(f"DATA: {json.dumps(data, indent=2)}")
            print("-" * 40)
    
    print("\nChat sequence test completed successfully!")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_event_dispatcher())
    asyncio.run(test_chat_sequence())
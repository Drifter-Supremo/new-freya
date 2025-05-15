"""
Simple test script for the TopicExtractor.
"""
import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from app
from app.services.topic_extraction import TopicExtractor

def main():
    # Create an instance of the TopicExtractor
    extractor = TopicExtractor()
    
    # Test messages
    test_messages = [
        "I love programming in Python and playing guitar on weekends.",
        "My job as a software engineer keeps me busy during the week.",
        "I'm feeling stressed about my upcoming exam next week.",
        "Do you have any recommendations for good Italian restaurants?",
        "I'm planning to buy a new laptop for programming and gaming.",
        "My family is coming to visit me next month and I'm excited to see them."
    ]
    
    print("Testing TopicExtractor with various messages:")
    for i, msg in enumerate(test_messages):
        topics = extractor.extract_topics(msg, top_n=3)
        print(f"\nMessage {i+1}: \"{msg}\"")
        print(f"Topics: {topics}")
    
    print("\nTopicExtractor test completed successfully!")

if __name__ == "__main__":
    main()

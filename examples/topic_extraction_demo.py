"""
Example script demonstrating how to use the TopicExtractor class.
"""
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.topic_extraction import TopicExtractor

def main():
    # Create an instance of the TopicExtractor
    extractor = TopicExtractor()
    
    # Example messages
    messages = [
        "I have a job interview tomorrow at Google for a software engineering position.",
        "I've been feeling really stressed and anxious about my health lately.",
        "I love playing guitar and hiking in the mountains on weekends.",
        "My mom and dad are coming to visit next week.",
        "I need to prepare for my final exams at university.",
        "I'm planning a trip to Japan next year.",
        "I've been cooking a lot of Italian food recently.",
        "I'm thinking about buying a new laptop for work.",
        "I'm feeling really happy and excited about my new job!",
        "I need to find a good restaurant for dinner tonight.",
        "I'm looking for a new apartment in the city center.",
        "I've been reading a great book about machine learning.",
        "I'm saving money to buy a new car next year.",
        "I'm feeling a bit lonely these days.",
        "I'm learning how to play the piano in my free time.",
    ]
    
    print("Topic Extraction Demo\n" + "=" * 50)
    
    for message in messages:
        # Extract topics from the message
        topics = extractor.extract_topics(message)
        
        # Print the results
        print(f'"{message}"')
        print(f'  Topics: {topics if topics else "No topics found"}')
        
        # Check if the message is about specific topics
        for topic in ["work", "health", "hobbies", "family"]:
            if extractor.is_about_topic(message, topic):
                print(f'  Is about {topic}: Yes')
        
        print()  # Add a blank line between messages

if __name__ == "__main__":
    main()

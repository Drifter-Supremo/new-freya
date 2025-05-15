from typing import List, Dict, Tuple
import re
from collections import defaultdict

class TopicExtractor:
    """
    A service for extracting topics from user messages based on predefined categories and keywords.
    This is part of the Tier 3: Topic Memory system.
    """
    
    def __init__(self):
        # Define common topics and their associated keywords
        self.common_topics = {
            "work": ["job", "work", "career", "company", "boss", "office", "colleague", 
                   "coworker", "project", "deadline", "meeting", "interview", "promotion", 
                   "salary", "profession"],
            "health": ["health", "sick", "illness", "disease", "doctor", "hospital", 
                     "symptom", "medicine", "pain", "injury", "exercise", "diet", "sleep", 
                     "stress", "anxiety", "depression"],
            "family": ["family", "parent", "father", "mother", "dad", "mom", "brother", 
                     "sister", "sibling", "child", "son", "daughter", "grandparent", 
                     "grandmother", "grandfather", "aunt", "uncle", "cousin", "niece", "nephew"],
            "relationships": ["relationship", "friend", "girlfriend", "boyfriend", "partner", 
                           "spouse", "husband", "wife", "date", "dating", "marriage", "wedding", 
                           "divorce", "love", "breakup"],
            "hobbies": ["hobby", "interest", "game", "sport", "book", "movie", "music", "art", 
                      "travel", "cook", "cooking", "photography", "garden", "gardening", 
                      "fishing", "hiking", "camping", "painting", "drawing", "craft"],
            "education": ["school", "college", "university", "class", "course", "degree", 
                        "study", "student", "professor", "teacher", "exam", "test", "grade", 
                        "education", "learn", "learning", "homework", "assignment"],
            "technology": ["technology", "computer", "phone", "laptop", "app", "software", 
                         "hardware", "internet", "website", "code", "programming", "data", 
                         "tech", "digital", "device", "gadget"],
            "finance": ["money", "finance", "financial", "bank", "invest", "investment", 
                      "save", "savings", "spend", "spending", "budget", "debt", "loan", 
                      "mortgage", "rent", "tax", "taxes", "income", "expense", "expenses"],
            "travel": ["travel", "trip", "vacation", "holiday", "flight", "hotel", "city", 
                     "country", "destination", "tour", "tourist", "passport", "journey", 
                     "visit", "beach", "mountain", "hiking"],
            "food": ["food", "eat", "eating", "restaurant", "meal", "breakfast", "lunch", 
                   "dinner", "snack", "cook", "cooking", "recipe", "ingredient", "dish", 
                   "taste", "flavor", "cuisine", "diet"],
            "housing": ["house", "home", "apartment", "flat", "rent", "mortgage", "room", 
                      "living", "move", "moving", "roommate", "neighbor", "neighborhood", 
                      "furniture", "decorate", "decoration", "renovation"],
            "entertainment": ["movie", "film", "tv", "television", "show", "series", "book", 
                           "novel", "read", "reading", "music", "song", "concert", "game", 
                           "gaming", "video game", "play", "stream", "streaming"],
            "personal": ["feel", "feeling", "emotion", "happy", "sad", "angry", "excited", 
                       "worried", "stress", "stressed", "anxious", "depressed", "lonely", 
                       "tired", "exhausted", "overwhelmed", "confident", "proud", "guilty", "shame"],
            "future": ["future", "plan", "planning", "goal", "dream", "aspiration", "hope", 
                     "change", "decision", "choice", "opportunity", "challenge", "obstacle", 
                     "problem", "solution"]
        }
        
        # Compile regex patterns for each keyword to match whole words only
        self.topic_patterns = {
            topic: [re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE) 
                  for keyword in keywords]
            for topic, keywords in self.common_topics.items()
        }
    
    def extract_topics(self, message: str, top_n: int = 3) -> List[str]:
        """
        Extract the most relevant topics from a message based on keyword matching.
        
        Args:
            message: The input text to analyze for topics
            top_n: Maximum number of topics to return (default: 3)
            
        Returns:
            List of topic strings, ordered by relevance (highest first)
        """
        if not message or not isinstance(message, str):
            return []
            
        # Convert message to lowercase for case-insensitive matching
        message_lower = message.lower()
        
        # Initialize scores for all topics
        topic_scores = defaultdict(int)
        
        # Score each topic based on keyword matches
        for topic, patterns in self.topic_patterns.items():
            for pattern in patterns:
                # Count occurrences of each keyword pattern
                matches = len(pattern.findall(message_lower))
                if matches > 0:
                    topic_scores[topic] += matches
        
        # If no topics found, return empty list
        if not topic_scores:
            return []
        
        # Sort topics by score (descending) and get top N
        sorted_topics = sorted(
            topic_scores.items(),
            key=lambda x: (-x[1], x[0])  # Sort by score desc, then by topic name
        )
        
        # Return just the topic names, but only those with at least one match
        return [topic for topic, score in sorted_topics if score > 0][:top_n]
    
    def is_about_topic(self, message: str, topic: str) -> bool:
        """
        Check if a message is about a specific topic.
        
        Args:
            message: The message to check
            topic: The topic to check against
            
        Returns:
            True if the message is about the topic, False otherwise
        """
        if not message or not isinstance(message, str) or topic not in self.topic_patterns:
            return False
            
        # Convert message to lowercase for case-insensitive matching
        message_lower = message.lower()
            
        # Check if any of the topic's keywords are in the message
        for keyword in self.common_topics[topic]:
            # Use word boundaries to match whole words only
            if re.search(rf'\b{re.escape(keyword)}\b', message_lower):
                return True
                
        return False


# Singleton instance for easy import
topic_extractor = TopicExtractor()

# Example usage:
if __name__ == "__main__":
    # Example usage
    extractor = TopicExtractor()
    test_messages = [
        "I love playing guitar and hiking in the mountains on weekends.",
        "My job as a software engineer keeps me busy during the week.",
        "I'm feeling really stressed about my upcoming exam next week.",
        "Do you have any recommendations for good Italian restaurants?"
    ]
    
    for msg in test_messages:
        topics = extractor.extract_topics(msg)
        print(f'"{msg}" -> Topics: {topics}')

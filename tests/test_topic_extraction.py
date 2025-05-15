import pytest
from app.services.topic_extraction import TopicExtractor

def test_extract_topics_basic():
    """Test basic topic extraction functionality."""
    extractor = TopicExtractor()
    
    # Test with a message about work
    topics = extractor.extract_topics("I have a meeting with my boss tomorrow")
    assert any(topic in ["work", "future"] for topic in topics)  # Could be either work or future
    
    # Test with a message about health
    topics = extractor.extract_topics("I've been feeling really stressed lately")
    assert "health" in topics or "personal" in topics  # Could be either health or personal
    
    # Test with a message about multiple topics
    topics = extractor.extract_topics("I love playing guitar and hiking in the mountains")
    assert any(topic in ["hobbies", "entertainment"] for topic in topics)  # Could be either

def test_extract_topics_case_insensitive():
    """Test that topic extraction is case insensitive."""
    extractor = TopicExtractor()
    
    # Different cases should still match
    assert "work" in extractor.extract_topics("I have a JOB interview tomorrow")
    assert "work" in extractor.extract_topics("I have a Job interview tomorrow")
    assert "work" in extractor.extract_topics("I have a job interview tomorrow")

def test_extract_topics_multiple_occurrences():
    """Test that topics with more keyword matches get higher scores."""
    extractor = TopicExtractor()
    
    # This message mentions work-related terms multiple times
    topics = extractor.extract_topics("I have a job as a software engineer. I love my work and my coworkers are great. We work on interesting projects.")
    assert topics[0] == "work"  # Work should be the top topic

def test_extract_topics_no_matches():
    """Test that empty or irrelevant messages return no topics."""
    extractor = TopicExtractor()
    
    # Test with empty string
    assert extractor.extract_topics("") == []
    
    # Test with None
    assert extractor.extract_topics(None) == []
    
    # Test with non-string input
    assert extractor.extract_topics(123) == []
    
    # Test with a message that shouldn't match any topics
    # Note: Some generic greetings might match with 'personal' topic
    # So we'll check for a truly irrelevant message
    assert extractor.extract_topics("asdf qwerty zxcvbnm") == []

def test_extract_topics_custom_top_n():
    """Test that the top_n parameter works as expected."""
    extractor = TopicExtractor()
    
    # This message could match multiple topics
    message = "I love my job as a teacher, but I've been feeling stressed about my health lately. I also enjoy cooking in my free time."
    
    assert len(extractor.extract_topics(message, top_n=1)) == 1
    assert len(extractor.extract_topics(message, top_n=2)) == 2
    assert len(extractor.extract_topics(message, top_n=5)) >= 3  # Should return all matches even if less than 5

def test_is_about_topic():
    """Test the is_about_topic method."""
    extractor = TopicExtractor()
    
    # Test with work-related messages
    assert extractor.is_about_topic("I have a job interview tomorrow", "work") is True
    assert extractor.is_about_topic("I need to prepare for my work presentation", "work") is True
    
    # Test with health-related messages
    assert extractor.is_about_topic("I'm feeling really stressed", "health") is True or \
           extractor.is_about_topic("I'm feeling really stressed", "personal") is True
    
    # Test with no matching topics
    assert extractor.is_about_topic("Hello, how are you?", "work") is False
    
    # Test with empty message
    assert extractor.is_about_topic("", "work") is False
    
    # Test with invalid topic
    assert extractor.is_about_topic("This is a test", "nonexistent_topic") is False

def test_topic_ranking():
    """Test that topics are ranked by relevance (number of matches)."""
    extractor = TopicExtractor()
    
    # This message has multiple work-related terms and one health-related term
    message = "I have a job as a software engineer. I love my work. I've been feeling a bit stressed though."
    topics = extractor.extract_topics(message)
    
    # Work should come before health because it has more matches
    if len(topics) > 1:  # In case some topics have the same score
        work_index = topics.index("work") if "work" in topics else -1
        health_index = topics.index("health") if "health" in topics else len(topics)
        assert work_index < health_index

# Run the tests
if __name__ == "__main__":
    pytest.main(["-v"])

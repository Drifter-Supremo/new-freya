class MockTopicExtractor:
    def extract_topics(self, text: str, top_n: int = 3) -> list[str]:
        """Mock implementation of topic extraction."""
        # Simple keyword-based extraction for testing
        text_lower = text.lower()
        topics = []
        
        if "programming" in text_lower or "python" in text_lower or "javascript" in text_lower:
            topics.append("programming")
        if "python" in text_lower:
            topics.append("python")
        if "javascript" in text_lower:
            topics.append("javascript")
        if "hiking" in text_lower or "mountains" in text_lower:
            topics.append("hiking")
        if "guitar" in text_lower:
            topics.append("music")
            
        return topics[:top_n]

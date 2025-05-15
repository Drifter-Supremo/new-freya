"""
Regex patterns for extracting user facts from messages.
Direct port of legacy Node.js implementation to Python.
"""

import re

# Pre-compile regex patterns for efficiency
USER_FACT_PATTERNS = {
    "job": [
        # Simple company patterns
        re.compile(r"(?:I|my)\s+work\s+at\s+([^,\.]+)", re.I),
        re.compile(r"(?:my)\s+job\s+(?:is\s+)?at\s+([^,\.]+)", re.I),
        re.compile(r"(?:I'?m?\s+)?working\s+at\s+([^,\.]+)", re.I),
        # Combined company and role patterns
        re.compile(r"(?:I|my)\s+work\s+at\s+([^,\.]+?)\s+(?:and|where|&)\s+(?:I\s+)?(?:work\s+(?:with|on|in)|do)\s+([^,\.]+)", re.I),
        re.compile(r"(?:I'?m?\s+)?working\s+at\s+([^,\.]+?)\s+(?:and|where|&)\s+(?:I\s+)?(?:work\s+(?:with|on|in)|do)\s+([^,\.]+)", re.I),
        # Role with company patterns
        re.compile(r"(?:I\s+am|I'm)\s+(?:an?\s+)?([^,\.]+?)\s+at\s+([^,\.]+)", re.I),
        re.compile(r"(?:I|me)\s+work\s+as\s+(?:an?\s+)?([^,\.]+?)\s+(?:at|for)\s+([^,\.]+)", re.I),
        # Simple role patterns
        re.compile(r"(?:I|my)\s+work\s+as\s+(?:an?\s+)?([^,\.]+)", re.I),
        re.compile(r"(?:I\s+am|I'm)\s+(?:an?\s+)?([^,\.]+?)\s+(?:by\s+profession|by\s+trade)", re.I)
    ],
    "location": [
        # Current location
        re.compile(r"(?:I|my)\s+live\s+in\s+([^,.]+)", re.I),
        re.compile(r"(?:I\s+am|I'm)\s+from\s+([^,.]+)", re.I),
        re.compile(r"(?:my)\s+home\s+(?:is\s+)?in\s+([^,.]+)", re.I)
    ],
    "interests": [
        # Hobbies and activities
        re.compile(r"(?:I|my)\s+(?:like|love|enjoy)\s+([^,.]+)", re.I),
        re.compile(r"(?:my)\s+hobby\s+is\s+([^,.]+)", re.I),
        re.compile(r"(?:I'm|I\s+am)\s+interested\s+in\s+([^,.]+)", re.I)
    ],
    "family": [
        # Direct relations
        re.compile(r"(?:my)\s+(?:wife|husband|son|daughter|brother|sister|mom|dad)\s+(?:is|name\s+is)\s+([^,.]+)", re.I),
        re.compile(r"([^,.]+)\s+is\s+my\s+(?:wife|husband|son|daughter|brother|sister|mom|dad)", re.I),
        re.compile(r"(?:I\s+have\s+a)\s+(?:wife|husband|son|daughter|brother|sister)\s+named\s+([^,.]+)", re.I)
    ],
    "pets": [
        # Pet names and types
        re.compile(r"(?:my)\s+(?:dog|cat|pet)\s+(?:is|name\s+is)\s+([^,.]+)", re.I),
        re.compile(r"([^,.]+)\s+is\s+my\s+(?:dog|cat|pet)", re.I),
        re.compile(r"(?:I\s+have\s+a)\s+(?:dog|cat|pet)\s+named\s+([^,.]+)", re.I)
    ],
    "preferences": [
        # Likes and favorites
        re.compile(r"(?:I|my)\s+(?:like|love|prefer)\s+([^,.]+)", re.I),
        re.compile(r"(?:my)\s+favorite\s+(?:food|color|movie|book|song)\s+is\s+([^,.]+)", re.I),
        re.compile(r"(?:I|my)\s+(?:hate|dislike|can't\s+stand)\s+([^,.]+)", re.I)
    ]
}

# Memory query patterns for topic-based retrieval
MEMORY_QUERY_PATTERNS = [
    re.compile(r"(?:do\s+you\s+)?(?:remember|recall|know)\s+(?:when|what|how|where|why|who|if|that|about|our|my|the)\s+([^?]+)", re.I),
    re.compile(r"(?:what|who|where|when|how)\s+(?:did|do|does|is|was|were)\s+(?:I|we|my|you|us|our)\s+([^?]+?)(?:\s+again|\s+before)?", re.I),
    re.compile(r"(?:tell|ask|talk)\s+(?:to|with)?\s+(?:me|us|you)\s+(?:again|more)?\s+(?:about|regarding|concerning|on)\s+([^?]+)", re.I),
    re.compile(r"(?:have\s+I|did\s+I|I've)\s+(?:ever|already|previously|before)\s+(?:told|mentioned|said|talked|spoke|discussed)\s+(?:to\s+you)?\s+(?:about|regarding|concerning|on)\s+([^?]+)", re.I),
    re.compile(r"(?:have|has|did)\s+(?:we|you|I)\s+(?:ever|already|previously|before)\s+(?:discussed|talked|spoken|had\s+a\s+conversation)\s+(?:about|regarding|concerning|on)\s+([^?]+)", re.I)
]
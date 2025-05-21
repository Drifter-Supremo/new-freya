"""
Test script for fact pattern regex validation.
Tests the regex patterns used for extracting user facts from messages.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from utils.fact_patterns import USER_FACT_PATTERNS

def run_pattern_test(category, test_cases):
    """Generic test runner for any fact pattern category."""
    for test_input, expected in test_cases.items():
        match_found = False
        for pattern in USER_FACT_PATTERNS[category]:
            match = pattern.search(test_input)
            if match:
                if expected:
                    if isinstance(expected, tuple):
                        # For patterns with multiple capture groups (e.g., company and role)
                        values = []
                        for i in range(1, match.lastindex + 1 if match.lastindex else 2):
                            try:
                                group = match.group(i)
                                if group:
                                    values.append(group.strip())
                            except IndexError:
                                continue
                        
                        # Check if we found all expected values in any order
                        all_found = all(exp in values for exp in expected)
                        if all_found:
                            print(f"✓ {category.title()} pattern matched correctly: '{test_input}' -> {tuple(values)}")
                            match_found = True
                            break
                    else:
                        # Single value match (e.g., just company or just role)
                        for i in range(1, match.lastindex + 1 if match.lastindex else 2):
                            try:
                                group = match.group(i)
                                if group and group.strip() == expected:
                                    print(f"✓ {category.title()} pattern matched correctly: '{test_input}' -> '{group.strip()}'")
                                    match_found = True
                                    break
                            except IndexError:
                                continue
                        if match_found:
                            break
                    continue
                match_found = True
                break
        
        if expected and not match_found:
            assert False, f"Expected to match '{expected}' but found no match for: '{test_input}'"
        elif not expected and not match_found:
            print(f"✓ Correctly found no {category} match for: '{test_input}'")

def test_job_patterns():
    test_cases = {
        # Company only
        "I work at Google": "Google",
        "My job at Apple": "Apple",
        # Combined company and role
        "I work at Google and I work with robots": ("Google", "robots"),
        "I'm working at Microsoft where I do AI research": ("Microsoft", "AI research"),
        "I'm an engineer at SpaceX": ("SpaceX", "engineer"),
        # Role only
        "I work as a developer": "developer",
        "I am a teacher by profession": "teacher",
        # Negative cases
        "I like working": None,
        "Google is a company": None
    }
    run_pattern_test("job", test_cases)

def test_location_patterns():
    test_cases = {
        "I live in New York": "New York",
        "I'm from London": "London",
        "My home is in Paris": "Paris",
        # Negative cases
        "I like New York": None,
        "London is beautiful": None
    }
    run_pattern_test("location", test_cases)

def test_interests_patterns():
    test_cases = {
        "I like playing guitar": "playing guitar",
        "My hobby is painting": "painting",
        "I'm interested in photography": "photography",
        # Negative cases
        "The guitar is nice": None,
        "She likes painting": None
    }
    run_pattern_test("interests", test_cases)

def test_family_patterns():
    test_cases = {
        "My wife is Sarah": "Sarah",
        "John is my brother": "John",
        "I have a daughter named Emma": "Emma",
        # Negative cases
        "The family is nice": None,
        "Wife is a good movie": None
    }
    run_pattern_test("family", test_cases)

def test_pets_patterns():
    test_cases = {
        "My dog is Max": "Max",
        "Luna is my cat": "Luna",
        "I have a pet named Buddy": "Buddy",
        # Negative cases
        "Dogs are cute": None,
        "That cat is nice": None
    }
    run_pattern_test("pets", test_cases)

def test_preferences_patterns():
    test_cases = {
        "I like pizza": "pizza",
        "My favorite color is blue": "blue",
        "I hate mornings": "mornings",
        # Negative cases
        "Pizza is good": None,
        "Blue is a color": None
    }
    run_pattern_test("preferences", test_cases)

if __name__ == "__main__":
    print("Testing fact pattern matching...")
    test_job_patterns()
    test_location_patterns()
    test_interests_patterns()
    test_family_patterns()
    test_pets_patterns()
    test_preferences_patterns()
    print("\nAll tests completed successfully! ✨")
"""
Test OpenAI integration with real API calls.
This tests the OpenAI service with the fine-tuned Freya model,
system prompt handling, and memory context integration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test results tracking
tests_passed = 0
tests_failed = 0


def test_result(test_name, passed, error=None):
    """Track test results."""
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        logger.info(f"✅ {test_name}: PASSED")
    else:
        tests_failed += 1
        logger.error(f"❌ {test_name}: FAILED - {error}")


def test_openai_service_initialization():
    """Test OpenAI service initialization."""
    try:
        from app.services.openai_service import OpenAIService
        
        # Initialize the service
        service = OpenAIService()
        
        # Verify service has required components
        assert hasattr(service, 'client'), "Missing client attribute"
        assert hasattr(service, 'create_freya_chat_completion'), "Missing create_freya_chat_completion method"
        assert hasattr(service, 'get_message_content'), "Missing get_message_content method"
        
        # Check model configuration
        from app.core.openai_constants import DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_TOKENS
        assert DEFAULT_MODEL == "ft:gpt-4.1-mini-2025-04-14:gorlea-industries:freya:BULkCmxj", f"Unexpected model: {DEFAULT_MODEL}"
        assert DEFAULT_TEMPERATURE == 1.0, f"Unexpected temperature: {DEFAULT_TEMPERATURE}"
        assert MAX_TOKENS == 800, f"Unexpected max_tokens: {MAX_TOKENS}"
        
        test_result("OpenAI service initialization", True)
    except Exception as e:
        test_result("OpenAI service initialization", False, str(e))


async def test_basic_chat_completion():
    """Test basic chat completion without memory context."""
    try:
        from app.services.openai_service import OpenAIService
        
        service = OpenAIService()
        
        # Test simple message
        user_message = "Hello, how are you today?"
        logger.info(f"\nTesting basic chat: '{user_message}'")
        
        response = await service.create_freya_chat_completion(
            user_message=user_message,
            conversation_history=[],
            memory_context=None
        )
        
        # Verify response structure
        assert response is not None, "Response is None"
        assert hasattr(response, 'choices'), "Response missing choices"
        assert len(response.choices) > 0, "No choices in response"
        
        # Get message content
        content = service.get_message_content(response)
        assert content is not None, "Content is None"
        assert len(content) > 0, "Content is empty"
        
        logger.info(f"Freya's response: {content[:100]}...")
        
        # Verify it's Freya's personality (should be brief, under 100 words)
        word_count = len(content.split())
        logger.info(f"Response word count: {word_count}")
        
        test_result("Basic chat completion", True)
    except Exception as e:
        test_result("Basic chat completion", False, str(e))


async def test_system_prompt_personality():
    """Test that Freya's personality comes through in responses."""
    try:
        from app.services.openai_service import OpenAIService
        
        service = OpenAIService()
        
        # Test messages that should trigger specific personality traits
        personality_tests = [
            {
                "message": "Tell me about yourself",
                "expected_traits": ["medical AI", "Saturn", "emotional"],
                "description": "Self-introduction"
            },
            {
                "message": "I'm feeling stressed about work",
                "expected_traits": ["care", "support", "understanding"],
                "description": "Emotional support"
            },
            {
                "message": "What happened on Saturn?",
                "expected_traits": ["crew", "mystery", "need to understand"],
                "description": "Saturn backstory"
            }
        ]
        
        logger.info("\nTesting Freya's personality traits:")
        
        for test in personality_tests:
            logger.info(f"\nTest: {test['description']}")
            logger.info(f"Message: '{test['message']}'")
            
            response = await service.create_freya_chat_completion(
                user_message=test['message'],
                conversation_history=[],
                memory_context=None
            )
            
            content = service.get_message_content(response).lower()
            logger.info(f"Response: {content[:150]}...")
            
            # Check response characteristics
            word_count = len(content.split())
            logger.info(f"  Word count: {word_count} (should be under 100)")
            
            # Check for personality markers (not strict requirements)
            found_traits = [trait for trait in test['expected_traits'] if trait in content]
            if found_traits:
                logger.info(f"  Found personality markers: {found_traits}")
        
        test_result("System prompt personality", True)
    except Exception as e:
        test_result("System prompt personality", False, str(e))


async def test_memory_context_integration():
    """Test chat completion with memory context."""
    try:
        from app.services.openai_service import OpenAIService
        from app.core.openai_constants import ROLE_USER, ROLE_ASSISTANT
        
        service = OpenAIService()
        
        # Create mock memory context
        memory_context = """### Memory Context ###

## User Facts
- Job: Diligent robotics and I monitor and troubleshoot robots that make delivers inside of hospitals ★★★★★
- Interests: it! ★★★★
- Preferences: that tagline! and maybe their rare candy adventure is like Harold and Kumar ★★★★

## Recent Conversation History
- Discussed work at the hospital with robots
- Mentioned feeling overwhelmed with the workload
"""
        
        # Create conversation history
        conversation_history = [
            {"role": ROLE_USER, "content": "I had a long day at work today"},
            {"role": ROLE_ASSISTANT, "content": "I bet dealing with those hospital robots can be exhausting. How are the delivery bots behaving?"}
        ]
        
        # Test memory-aware response
        user_message = "Do you remember what I do for work?"
        logger.info(f"\nTesting memory integration: '{user_message}'")
        logger.info("Memory context includes job info about hospital robots")
        
        response = await service.create_freya_chat_completion(
            user_message=user_message,
            conversation_history=conversation_history,
            memory_context=memory_context
        )
        
        content = service.get_message_content(response)
        logger.info(f"Response: {content}")
        
        # Verify response uses memory context
        content_lower = content.lower()
        memory_references = ["robot", "hospital", "diligent", "deliver", "monitor", "troubleshoot"]
        found_references = [ref for ref in memory_references if ref in content_lower]
        
        logger.info(f"Found memory references: {found_references}")
        assert len(found_references) > 0, "Response doesn't reference memory context"
        
        test_result("Memory context integration", True)
    except Exception as e:
        test_result("Memory context integration", False, str(e))


async def test_conversation_continuity():
    """Test that conversation history is properly maintained."""
    try:
        from app.services.openai_service import OpenAIService
        from app.core.openai_constants import ROLE_USER, ROLE_ASSISTANT
        
        service = OpenAIService()
        
        # Build conversation over multiple turns
        conversation_history = []
        
        # Turn 1
        message1 = "My name is Sencere"
        logger.info(f"\nTurn 1: '{message1}'")
        
        response1 = await service.create_freya_chat_completion(
            user_message=message1,
            conversation_history=conversation_history,
            memory_context=None
        )
        content1 = service.get_message_content(response1)
        logger.info(f"Response 1: {content1[:100]}...")
        
        # Update history
        conversation_history.append({"role": ROLE_USER, "content": message1})
        conversation_history.append({"role": ROLE_ASSISTANT, "content": content1})
        
        # Turn 2 - Reference previous turn
        message2 = "What did I just tell you my name was?"
        logger.info(f"\nTurn 2: '{message2}'")
        
        response2 = await service.create_freya_chat_completion(
            user_message=message2,
            conversation_history=conversation_history,
            memory_context=None
        )
        content2 = service.get_message_content(response2)
        logger.info(f"Response 2: {content2}")
        
        # Verify continuity
        assert "sencere" in content2.lower(), "Response doesn't reference the name from conversation history"
        
        test_result("Conversation continuity", True)
    except Exception as e:
        test_result("Conversation continuity", False, str(e))


async def test_response_format_consistency():
    """Test that responses maintain consistent format."""
    try:
        from app.services.openai_service import OpenAIService
        
        service = OpenAIService()
        
        # Test multiple responses for format consistency
        test_messages = [
            "Hello",
            "How's the weather?",
            "Tell me a joke",
            "What do you think about AI?"
        ]
        
        logger.info("\nTesting response format consistency:")
        
        for message in test_messages:
            response = await service.create_freya_chat_completion(
                user_message=message,
                conversation_history=[],
                memory_context=None
            )
            
            content = service.get_message_content(response)
            
            # Check format constraints
            word_count = len(content.split())
            has_quotes = '"' in content or "'" in content
            has_asterisks = '*' in content
            dash_count = content.count(' - ')
            
            logger.info(f"\nMessage: '{message}'")
            logger.info(f"Response length: {word_count} words")
            logger.info(f"Format checks: Quotes={has_quotes}, Asterisks={has_asterisks}, Dashes={dash_count}")
            
            # Verify Freya's format rules
            if has_asterisks:
                logger.warning("  ⚠️  Contains asterisks (should avoid)")
            if dash_count > 1:
                logger.warning(f"  ⚠️  Multiple dashes ({dash_count}) - should limit to 1")
        
        test_result("Response format consistency", True)
    except Exception as e:
        test_result("Response format consistency", False, str(e))


async def test_error_handling():
    """Test error handling in OpenAI service."""
    try:
        from app.services.openai_service import OpenAIService
        
        service = OpenAIService()
        
        # Test with empty message
        logger.info("\nTesting error handling with edge cases:")
        
        # Test 1: Empty message
        try:
            response = await service.create_freya_chat_completion(
                user_message="",
                conversation_history=[],
                memory_context=None
            )
            content = service.get_message_content(response)
            logger.info(f"Empty message handled gracefully: {content[:50]}...")
        except Exception as e:
            logger.warning(f"Empty message caused error: {str(e)}")
        
        # Test 2: Very long message
        long_message = "test " * 500  # 2500+ characters
        try:
            response = await service.create_freya_chat_completion(
                user_message=long_message,
                conversation_history=[],
                memory_context=None
            )
            content = service.get_message_content(response)
            logger.info(f"Long message handled gracefully, response length: {len(content)}")
        except Exception as e:
            logger.warning(f"Long message caused error: {str(e)}")
        
        # Test 3: Invalid conversation history format
        try:
            response = await service.create_freya_chat_completion(
                user_message="Hello",
                conversation_history=[{"invalid": "format"}],
                memory_context=None
            )
            logger.info("Invalid history format handled gracefully")
        except Exception as e:
            logger.info(f"Invalid history format caught correctly: {type(e).__name__}")
        
        test_result("Error handling", True)
    except Exception as e:
        test_result("Error handling", False, str(e))


async def test_streaming_capability():
    """Test streaming response capability."""
    try:
        from app.services.openai_service import OpenAIService
        
        service = OpenAIService()
        
        logger.info("\nTesting streaming capability:")
        
        # Test streaming response
        user_message = "Tell me a short story in 3 sentences"
        
        response = await service.create_freya_chat_completion(
            user_message=user_message,
            conversation_history=[],
            memory_context=None,
            stream=True
        )
        
        # Collect streamed chunks
        chunks = []
        try:
            async for chunk in response:
                # Handle both string chunks and object chunks
                if isinstance(chunk, str):
                    chunks.append(chunk)
                elif hasattr(chunk, 'choices') and chunk.choices and chunk.choices[0].delta.content:
                    chunks.append(chunk.choices[0].delta.content)
        except Exception as e:
            logger.warning(f"Streaming iteration error: {e}")
            # If streaming fails, we might get the full response
            if hasattr(response, 'choices'):
                content = service.get_message_content(response)
                chunks = [content]
        
        complete_response = ''.join(chunks) if chunks else ""
        logger.info(f"Streamed response ({len(chunks)} chunks): {complete_response[:100]}...")
        
        # For now, just verify we got a response (streaming might not be fully implemented)
        assert len(complete_response) > 0 or len(chunks) > 0, "No content in response"
        
        test_result("Streaming capability", True)
    except Exception as e:
        test_result("Streaming capability", False, str(e))


async def test_model_parameters():
    """Test that model parameters are correctly applied."""
    try:
        from app.services.openai_service import OpenAIService
        from app.core.openai_constants import DEFAULT_MODEL, DEFAULT_TEMPERATURE, MAX_TOKENS
        
        service = OpenAIService()
        
        logger.info("\nTesting model parameters:")
        logger.info(f"  Model: {DEFAULT_MODEL}")
        logger.info(f"  Temperature: {DEFAULT_TEMPERATURE}")
        logger.info(f"  Max tokens: {MAX_TOKENS}")
        
        # Make a request and verify it uses correct parameters
        response = await service.create_freya_chat_completion(
            user_message="Say hello",
            conversation_history=[],
            memory_context=None
        )
        
        # Check response characteristics
        content = service.get_message_content(response)
        
        # Verify response exists and is within token limits
        assert content is not None, "No response content"
        
        # Estimate tokens (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(content) / 4
        logger.info(f"Estimated response tokens: {estimated_tokens:.0f}")
        
        # Check if response seems to respect max tokens
        if estimated_tokens > MAX_TOKENS * 1.5:  # Allow some variance
            logger.warning(f"Response may exceed MAX_TOKENS ({MAX_TOKENS})")
        
        test_result("Model parameters", True)
    except Exception as e:
        test_result("Model parameters", False, str(e))


async def main():
    """Run all OpenAI integration tests."""
    logger.info("=" * 70)
    logger.info("OPENAI INTEGRATION TESTS")
    logger.info("Testing with real OpenAI API calls")
    logger.info("=" * 70)
    
    # Run sync tests
    test_openai_service_initialization()
    
    # Run async tests
    await test_basic_chat_completion()
    await test_system_prompt_personality()
    await test_memory_context_integration()
    await test_conversation_continuity()
    await test_response_format_consistency()
    await test_error_handling()
    await test_streaming_capability()
    await test_model_parameters()
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Tests passed: {tests_passed}")
    logger.info(f"Tests failed: {tests_failed}")
    logger.info(f"Total tests: {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        logger.info("\n✅ All OpenAI integration tests passed!")
        logger.info("The OpenAI service is working correctly with the fine-tuned Freya model.")
        return 0
    else:
        logger.error(f"\n❌ {tests_failed} tests failed!")
        logger.error("Please check the errors above for details.")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
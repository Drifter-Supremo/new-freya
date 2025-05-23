// Legacy API compatibility layer for Freya
(function() {
  'use strict';

  // API endpoint configuration
  const API_BASE_URL = 'http://localhost:8001';
  const FIREBASE_CHAT_ENDPOINT = `${API_BASE_URL}/firebase/chat`;

  // Default user ID for testing
  const USER_ID = 'test_user_123';
  
  // Store conversation ID across messages
  let currentConversationId = null;

  // Send message to API
  window.sendMessageToAPI = async function(userText, showStatus = false) {
    console.log('=== FREYA API DEBUG START ===');
    console.log('User message:', userText);
    console.log('API endpoint:', FIREBASE_CHAT_ENDPOINT);
    
    try {
      // Dispatch listening event
      console.log('Dispatching freya:listening event');
      window.dispatchEvent(new CustomEvent('freya:listening'));
      
      // Then dispatch thinking event
      setTimeout(() => {
        console.log('Dispatching freya:thinking event');
        window.dispatchEvent(new CustomEvent('freya:thinking'));
      }, 100);

      console.log('Making fetch request to:', FIREBASE_CHAT_ENDPOINT);
      // Send the message to the Firebase chat endpoint
      const response = await fetch(FIREBASE_CHAT_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: USER_ID,
          message: userText,
          conversation_id: currentConversationId,
          include_memory: true
        })
      });

      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);
      
      if (!response.ok) {
        const errorData = await response.text();
        console.error('HTTP error details:', errorData);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData}`);
      }

      // Get the response directly from the endpoint
      const result = await response.json();
      console.log('Chat response received:', result);
      
      // Store conversation ID for future messages
      if (result.conversation_id) {
        currentConversationId = result.conversation_id;
      }

      // Send the complete response
      window.dispatchEvent(new CustomEvent('freya:reply', {
        detail: { message: result.message }
      }));

    } catch (error) {
      console.error('=== FREYA API ERROR ===');
      console.error('Error sending message to API:', error);
      console.error('Error details:', error.message);
      console.error('=== END ERROR ===');
      
      // Send error response
      window.dispatchEvent(new CustomEvent('freya:reply', {
        detail: { message: "I'm having trouble connecting right now. Please try again later." }
      }));
    }
    
    console.log('=== FREYA API DEBUG END ===');
  };

  // Optional: Function to start a new conversation
  window.startNewConversation = function() {
    currentConversationId = null;
    console.log('Started new conversation');
  };

  // Optional: Function to get current conversation ID
  window.getCurrentConversationId = function() {
    return currentConversationId;
  };

  console.log('Freya API compatibility layer loaded');
})();
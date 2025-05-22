// Legacy API compatibility layer for Freya
(function() {
  'use strict';

  // API endpoint configuration
  const API_BASE_URL = 'http://localhost:8000';
  const FIREBASE_CHAT_ENDPOINT = `${API_BASE_URL}/firebase/chat`;

  // Default user ID for testing
  const USER_ID = 'test_user_123';
  
  // Store conversation ID across messages
  let currentConversationId = null;

  // Send message to API
  window.sendMessageToAPI = async function(userText, showStatus = false) {
    try {
      // Dispatch listening event
      window.dispatchEvent(new CustomEvent('freya:listening'));
      
      // Then dispatch thinking event
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('freya:thinking'));
      }, 100);

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

      if (!response.ok) {
        const errorData = await response.text();
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
      console.error('Error sending message to API:', error);
      
      // Send error response
      window.dispatchEvent(new CustomEvent('freya:reply', {
        detail: { message: "I'm having trouble connecting right now. Please try again later." }
      }));
    }
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
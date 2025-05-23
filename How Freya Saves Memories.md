How Freya Saves Memories

1. User Facts (Tier 1\) \- What Gets Saved  
- Pattern Matching: The system uses regex patterns in utils/fact\_patterns.py to automatically detect facts about users  
- Examples of what gets saved:  
  - Job information: "I work at a hospital" → Saves as job fact  
  - Family details: "I have two kids" → Saves as family fact  
  - Location: "I live in Austin" → Saves as location fact  
  - Preferences: "I love hiking" → Saves as interests/preferences  
- What doesn't get saved: Temporary states, opinions about movies/weather, general conversation  
2. Recent History (Tier 2\) \- Automatic Saving  
- Everything is saved: All messages in a conversation are automatically stored  
- No filtering: Both user messages and Freya's responses are saved  
- Time-limited: Only recent messages (last 30 days by default) are considered "recent"  
- Conversation-based: Messages are grouped by conversation ID  
3. Topic Memory (Tier 3\) \- Topic Extraction  
- Automatic extraction: Topics are extracted from conversations using keyword matching  
- Topic categories: Family, work, health, hobbies, education, location  
- Message tagging: Messages get tagged with relevant topics for later retrieval

How Freya Retrieves Memories

1. Memory Query Detection

The system first detects if a user is asking about memories using patterns like:

- "Do you remember..."  
- "What did I tell you about..."  
- "Have we talked about..."  
- "What do you know about my..."  
2. Context-Based Retrieval

When building context for a response, the system:

- Extracts topics from the user's current message  
- Scores relevance of stored memories to the current query  
- Prioritizes memories based on:  
  - Topic match score  
  - Recency (more recent \= higher priority)  
  - Fact type (job/family facts get higher weight)  
  - Query type (knowledge query vs. temporal query)  
3. Memory Assembly Process

For each user message:

1. Detect if it's a memory query (94.4% accuracy)  
2. Extract topics from the query  
3. Retrieve relevant facts that match the topics  
4. Get recent messages from conversation history  
5. Find topic memories that relate to the query  
6. Format everything into a memory context  
7. Send to OpenAI along with the user's message

What Makes It Smart

1. No Explicit "Save" Command: Users don't need to tell Freya to remember something \- it happens automatically  
2. Relevance Scoring: Not all memories are included in every response \- only relevant ones  
3. Memory Limits: The system limits memory context to avoid overwhelming the AI model  
4. Natural Integration: Memories are injected into the conversation context, so Freya naturally references them

Example Flow

User: "I just started a new job at Microsoft as a software engineer"

- System automatically extracts: job="software engineer at Microsoft"  
- Saves to userFacts collection  
- Tags conversation with "work" topic

Later... User: "Do you remember what I do for work?"

- System detects this is a memory query  
- Extracts topic: "work"  
- Retrieves the job fact  
- Includes in context: "Job: software engineer at Microsoft"  
- Freya responds: "Yeah, you're crushing it at Microsoft as a software engineer\!"

The beauty is that it all happens automatically \- Freya doesn't need to be programmed to save specific things, the pattern matching and topic extraction handle it naturally\!  

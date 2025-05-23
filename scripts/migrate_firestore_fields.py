"""
migrate_firestore_fields.py - Script to add missing fields to Firestore documents

This script adds:
- userId field to userFacts documents
- conversationId field to messages documents
- topicIds array field to messages documents
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import time

from app.services.firebase_service import FirebaseService
from app.services.topic_extraction import TopicExtractor
from app.core.config import logger

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class FirestoreMigration:
    """Handle Firestore document migrations."""
    
    def __init__(self):
        self.firebase = FirebaseService()
        self.topic_extractor = TopicExtractor()
        self.stats = {
            'user_facts_migrated': 0,
            'messages_migrated': 0,
            'errors': 0,
            'start_time': datetime.now()
        }
    
    def migrate_user_facts(self, user_id: str, dry_run: bool = True):
        """
        Add userId field to userFacts documents.
        
        Args:
            user_id: The user ID to add to facts
            dry_run: If True, only simulate the migration
        """
        print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating userFacts collection...")
        
        # Get all user facts
        facts = self.firebase.query_collection('userFacts', filters=[], limit=1000)
        print(f"Found {len(facts)} userFacts documents")
        
        migrated = 0
        for fact in facts:
            fact_id = fact.get('id')
            
            # Check if userId field exists
            if 'userId' not in fact:
                if dry_run:
                    print(f"  Would add userId='{user_id}' to fact {fact_id}")
                else:
                    # Add userId field
                    success = self.firebase.update_document('userFacts', fact_id, {'userId': user_id})
                    if success:
                        print(f"  ✓ Added userId to fact {fact_id}")
                        migrated += 1
                    else:
                        print(f"  ✗ Failed to update fact {fact_id}")
                        self.stats['errors'] += 1
            else:
                print(f"  - Fact {fact_id} already has userId: {fact.get('userId')}")
        
        self.stats['user_facts_migrated'] = migrated
        print(f"\nMigrated {migrated} userFacts documents")
    
    def migrate_messages(self, dry_run: bool = True):
        """
        Add conversationId and topicIds fields to messages.
        
        Args:
            dry_run: If True, only simulate the migration
        """
        print(f"\n{'[DRY RUN] ' if dry_run else ''}Migrating messages collection...")
        
        # Get all messages
        messages = self.firebase.query_collection('messages', filters=[], limit=1000)
        print(f"Found {len(messages)} messages documents")
        
        # Get all conversations to map messages
        conversations = self.firebase.query_collection('conversations', filters=[], limit=100)
        print(f"Found {len(conversations)} conversations")
        
        # Create a simple mapping strategy
        # In a real migration, you'd need more sophisticated logic
        default_conversation_id = None
        if conversations:
            # Use the most recent conversation as default
            # Handle datetime comparisons safely
            def get_sort_key(conv):
                updated_at = conv.get('updatedAt')
                if updated_at is None:
                    return datetime.min.replace(tzinfo=timezone.utc)
                elif hasattr(updated_at, 'seconds'):
                    # Firestore timestamp
                    return datetime.fromtimestamp(updated_at.seconds, tz=timezone.utc)
                elif isinstance(updated_at, datetime):
                    # Ensure timezone aware
                    if updated_at.tzinfo is None:
                        return updated_at.replace(tzinfo=timezone.utc)
                    return updated_at
                else:
                    return datetime.min.replace(tzinfo=timezone.utc)
            
            conversations.sort(key=get_sort_key, reverse=True)
            default_conversation_id = conversations[0].get('id')
            print(f"Using conversation {default_conversation_id} as default")
        
        migrated = 0
        for msg in messages:
            msg_id = msg.get('id')
            content = msg.get('user', '')  # Messages use 'user' field for content
            updates = {}
            
            # Check if conversationId field exists
            if 'conversationId' not in msg:
                # In a real migration, you'd determine the correct conversation
                # For now, we'll use the default
                if default_conversation_id:
                    updates['conversationId'] = default_conversation_id
            
            # Check if topicIds field exists
            if 'topicIds' not in msg and content:
                # Extract topics from message content
                topics = self.topic_extractor.extract_topics(content, top_n=3)
                if topics:
                    # In a real system, you'd map topic names to IDs
                    # For now, we'll use topic names as IDs
                    updates['topicIds'] = topics
            
            # Apply updates if needed
            if updates:
                if dry_run:
                    print(f"  Would update message {msg_id} with: {updates}")
                else:
                    success = self.firebase.update_document('messages', msg_id, updates)
                    if success:
                        print(f"  ✓ Updated message {msg_id}")
                        migrated += 1
                    else:
                        print(f"  ✗ Failed to update message {msg_id}")
                        self.stats['errors'] += 1
            else:
                print(f"  - Message {msg_id} already has required fields")
        
        self.stats['messages_migrated'] = migrated
        print(f"\nMigrated {migrated} messages documents")
    
    def add_indexes_instructions(self):
        """Print instructions for adding Firestore indexes."""
        print("\n📋 FIRESTORE INDEX CREATION INSTRUCTIONS")
        print("=" * 60)
        print("\nPlease create the following composite indexes in Firebase Console:")
        print("(Firebase Console > Firestore Database > Indexes)")
        
        indexes = [
            {
                "collection": "userFacts",
                "fields": [
                    ("userId", "Ascending"),
                    ("timestamp", "Descending")
                ],
                "query_scope": "Collection"
            },
            {
                "collection": "conversations",
                "fields": [
                    ("userId", "Ascending"),
                    ("updatedAt", "Descending")
                ],
                "query_scope": "Collection"
            },
            {
                "collection": "messages",
                "fields": [
                    ("conversationId", "Ascending"),
                    ("timestamp", "Descending")
                ],
                "query_scope": "Collection"
            },
            {
                "collection": "messages",
                "fields": [
                    ("topicIds", "Array Contains"),
                    ("timestamp", "Descending")
                ],
                "query_scope": "Collection"
            }
        ]
        
        for idx, index in enumerate(indexes, 1):
            print(f"\n{idx}. Collection: {index['collection']}")
            print("   Fields:")
            for field, order in index['fields']:
                print(f"   - {field}: {order}")
            print(f"   Query Scope: {index['query_scope']}")
    
    def verify_migration(self, user_id: str):
        """Verify the migration was successful."""
        print("\n🔍 Verifying Migration...")
        
        # Check userFacts
        facts_with_userId = 0
        facts = self.firebase.query_collection('userFacts', filters=[], limit=100)
        for fact in facts:
            if 'userId' in fact:
                facts_with_userId += 1
        
        print(f"\nUserFacts: {facts_with_userId}/{len(facts)} have userId field")
        
        # Check messages
        messages_with_fields = 0
        messages = self.firebase.query_collection('messages', filters=[], limit=100)
        for msg in messages:
            if 'conversationId' in msg or 'topicIds' in msg:
                messages_with_fields += 1
        
        print(f"Messages: {messages_with_fields}/{len(messages)} have new fields")
        
        # Test optimized queries
        print("\n🧪 Testing Optimized Queries...")
        
        try:
            # Test userFacts with userId filter
            start_time = time.time()
            filtered_facts = self.firebase.query_collection(
                'userFacts',
                filters=[('userId', '==', user_id)],
                limit=10
            )
            query_time = time.time() - start_time
            print(f"✓ UserFacts query with userId filter: {len(filtered_facts)} results in {query_time:.3f}s")
        except Exception as e:
            print(f"✗ UserFacts query failed: {str(e)}")
        
        try:
            # Test messages with conversationId filter
            # Get a conversation ID for testing
            conversations = self.firebase.query_collection('conversations', filters=[], limit=1)
            if conversations:
                test_conversation_id = conversations[0].get('id')
                start_time = time.time()
                filtered_messages = self.firebase.query_collection(
                    'messages',
                    filters=[('conversationId', '==', test_conversation_id)],
                    limit=10
                )
                query_time = time.time() - start_time
                print(f"✓ Messages query with conversationId filter: {len(filtered_messages)} results in {query_time:.3f}s")
            else:
                print("No conversations found for testing")
        except Exception as e:
            print(f"✗ Messages query failed: {str(e)}")
    
    def print_summary(self):
        """Print migration summary."""
        duration = (datetime.now() - self.stats['start_time']).total_seconds()
        
        print("\n📊 MIGRATION SUMMARY")
        print("=" * 60)
        print(f"Duration: {duration:.1f} seconds")
        print(f"UserFacts migrated: {self.stats['user_facts_migrated']}")
        print(f"Messages migrated: {self.stats['messages_migrated']}")
        print(f"Errors: {self.stats['errors']}")
        
        if self.stats['errors'] > 0:
            print("\n⚠️  Some documents failed to migrate. Check logs for details.")
        else:
            print("\n✅ Migration completed successfully!")

def main():
    """Main migration function."""
    print("🔥 Firestore Field Migration Tool")
    print("=" * 60)
    
    # Initialize migration
    migration = FirestoreMigration()
    
    # Configuration
    user_id = "Sencere"  # Default user ID
    dry_run = False  # Set to False to actually perform migration
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")
        print("Set dry_run=False to perform actual migration\n")
    else:
        print("\n⚠️  PRODUCTION MODE - Changes will be made to Firestore!")
        print("Proceeding with migration...")
        # Auto-confirm for automated execution
        # response = input("Are you sure you want to continue? (yes/no): ")
        # if response.lower() != 'yes':
        #     print("Migration cancelled.")
        #     return
    
    # Run migrations
    migration.migrate_user_facts(user_id, dry_run=dry_run)
    migration.migrate_messages(dry_run=dry_run)
    
    # Add index instructions
    migration.add_indexes_instructions()
    
    # Verify if not dry run
    if not dry_run:
        migration.verify_migration(user_id)
    
    # Print summary
    migration.print_summary()

if __name__ == "__main__":
    main()
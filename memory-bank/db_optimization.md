# Freya Backend: Database Optimization Tips

## 1. Indexing
- **Primary keys**: Automatically indexed (e.g., `id` fields).
- **Foreign keys**: Add indexes to `user_id`, `conversation_id`, `topic_id` in their respective tables for fast joins and lookups.
- **Composite indexes**:
  - On `MessageTopic(message_id, topic_id)` for efficient many-to-many queries.
  - On `Message(conversation_id, timestamp)` for fast retrieval of messages in a conversation, ordered by time.
- **Full-text search**: Consider a GIN index on message content or topic name if you plan to implement search features.

## 2. Constraints
- **Foreign key constraints**: Enforce referential integrity between related tables.
- **Unique constraints**: E.g., unique email for `User`, unique topic names in `Topic`.
- **Not null constraints**: On required fields (e.g., `content` in Message, `name` in User/Topic).

## 3. Query Optimization Tips
- **Pagination**: Use `LIMIT` and `OFFSET` for large result sets (e.g., messages in a conversation).
- **Selective columns**: Only select the columns you need in queries to minimize data transfer.
- **Batch operations**: Use bulk inserts/updates where possible.
- **Analyze and VACUUM**: Regularly run PostgreSQL's `ANALYZE` and `VACUUM` to keep query plans optimal.

## 4. Example Index Definitions (PostgreSQL)
```sql
CREATE INDEX idx_conversation_user_id ON Conversation(user_id);
CREATE INDEX idx_message_conversation_id ON Message(conversation_id);
CREATE INDEX idx_message_user_id ON Message(user_id);
CREATE INDEX idx_message_timestamp ON Message(conversation_id, timestamp);
CREATE UNIQUE INDEX idx_user_email ON User(email);
CREATE UNIQUE INDEX idx_topic_name ON Topic(name);
CREATE INDEX idx_message_topic ON MessageTopic(message_id, topic_id);
```

---

These optimizations will help your Freya backend remain fast, reliable, and scalable as your user base and message volume grow. Review and adjust indexes as your query patterns evolve.

## Migration Patterns

### Adding Non-Nullable Columns
When adding non-nullable columns to existing tables with data:
1. Add column as nullable first
2. Update existing rows with default values
3. Alter column to NOT NULL

Example:
```python
def upgrade():
    # First add the column as nullable
    op.add_column('messages', sa.Column('role', sa.String(20), nullable=True))
    # Update existing rows with a default role
    op.execute("UPDATE messages SET role = 'user' WHERE role IS NULL")
    # Now make the column NOT NULL
    op.alter_column('messages', 'role', nullable=False)
```

### Alembic Usage
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check current revision
alembic current
```

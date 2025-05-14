"""add tsvector column, GIN index, and trigger for message content full-text search

Revision ID: 20250514_fts_message_content
Revises: 02e11bc64aff
Create Date: 2025-05-14 15:33:54
"""
from alembic import op
import sqlalchemy as sa

revision = '20250514_fts_message_content'
down_revision = '02e11bc64aff'
branch_labels = None
depends_on = None

def upgrade():
    # Add the tsvector column
    op.add_column('messages', sa.Column('content_tsv', sa.dialects.postgresql.TSVECTOR))
    # Create the GIN index
    op.create_index('ix_messages_content_tsv', 'messages', ['content_tsv'], postgresql_using='gin')
    # Create the trigger function
    op.execute('''
    CREATE FUNCTION messages_content_tsv_trigger() RETURNS trigger AS $$
    begin
      new.content_tsv := to_tsvector('english', coalesce(new.content, ''));
      return new;
    end
    $$ LANGUAGE plpgsql;
    ''')
    # Create the trigger itself
    op.execute('''
    CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
    ON messages FOR EACH ROW EXECUTE FUNCTION messages_content_tsv_trigger();
    ''')
    # Backfill existing rows
    op.execute("UPDATE messages SET content_tsv = to_tsvector('english', coalesce(content, ''));")

def downgrade():
    op.execute('DROP TRIGGER IF EXISTS tsvectorupdate ON messages;')
    op.execute('DROP FUNCTION IF EXISTS messages_content_tsv_trigger();')
    op.drop_index('ix_messages_content_tsv', table_name='messages')
    op.drop_column('messages', 'content_tsv')

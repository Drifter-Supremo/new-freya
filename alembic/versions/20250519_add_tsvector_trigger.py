"""Add tsvector trigger for messages

Revision ID: 20250519_add_tsvector_trigger
Revises: 15978ec8d79b
Create Date: 2025-05-19

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250519_add_tsvector_trigger'
down_revision = '15978ec8d79b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create function to update tsvector
    op.execute("""
        CREATE OR REPLACE FUNCTION update_messages_content_tsv() RETURNS trigger AS $$
        begin
            new.content_tsv := to_tsvector('english', new.content);
            return new;
        end
        $$ LANGUAGE plpgsql;
    """)

    # Create trigger for messages table
    op.execute("""
        CREATE TRIGGER messages_content_tsv_update
        BEFORE INSERT OR UPDATE OF content ON messages
        FOR EACH ROW EXECUTE FUNCTION update_messages_content_tsv();
    """)

    # Update existing rows
    op.execute("""
        UPDATE messages 
        SET content_tsv = to_tsvector('english', content)
        WHERE content_tsv IS NULL;
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS messages_content_tsv_update ON messages;")
    op.execute("DROP FUNCTION IF EXISTS update_messages_content_tsv();")
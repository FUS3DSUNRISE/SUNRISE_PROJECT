"""add thumbnail path to prompt requests

Revision ID: a7b3f8d1c2e9
Revises: c9dad017f8e4

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a7b3f8d1c2e9"
down_revision = "c9dad017f8e4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("prompt_requests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("thumbnail_path", sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table("prompt_requests", schema=None) as batch_op:
        batch_op.drop_column("thumbnail_path")

"""switched default model to deepseek-ai/DeepSeek-V3

Revision ID: fe7f444c471c
Revises: fabe16a72c02
Create Date: 2025-05-11 15:03:20.801025

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fe7f444c471c'
down_revision = 'fabe16a72c02'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        'custom_ai',
        'ai_model',
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
        server_default=sa.text("'deepseek-ai/DeepSeek-V3'")
    )


def downgrade() -> None:
    op.alter_column(
        'custom_ai',
        'ai_model',
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
        server_default=sa.text("'mistralai/Mistral-7B-Instruct-v0.3'")
    )

"""Add stance to Comment

Revision ID: 8b8a7c4d2f1e
Revises: 698cac10eaa6
Create Date: 2026-05-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b8a7c4d2f1e'
down_revision = '698cac10eaa6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('stance', sa.String(length=20), nullable=False, server_default='neutral')
        )

    op.execute("""
        UPDATE comment
        SET stance = CASE (
            SELECT vote.vote_type
            FROM vote
            WHERE vote.user_id = comment.user_id
              AND vote.debate_id = comment.debate_id
            LIMIT 1
        )
            WHEN 'agree' THEN 'blue'
            WHEN 'disagree' THEN 'red'
            ELSE 'neutral'
        END
    """)

    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.alter_column('stance', server_default=None)


def downgrade():
    with op.batch_alter_table('comment', schema=None) as batch_op:
        batch_op.drop_column('stance')

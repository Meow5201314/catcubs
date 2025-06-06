"""添加公告Markdown支持

Revision ID: 47d0a9d6ce8e
Revises: e24c8daeb39f
Create Date: 2025-05-29 16:10:47.243948

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '47d0a9d6ce8e'
down_revision = 'e24c8daeb39f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('admin_logs', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=mysql.DATETIME(),
               nullable=True)

    with op.batch_alter_table('announcements', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_markdown', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('announcements', schema=None) as batch_op:
        batch_op.drop_column('is_markdown')

    with op.batch_alter_table('admin_logs', schema=None) as batch_op:
        batch_op.alter_column('created_at',
               existing_type=mysql.DATETIME(),
               nullable=False)

    # ### end Alembic commands ###

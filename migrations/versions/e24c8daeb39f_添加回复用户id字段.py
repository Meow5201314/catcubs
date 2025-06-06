"""添加回复用户ID字段

Revision ID: e24c8daeb39f
Revises: d2a8ee483146
Create Date: 2025-05-23 02:16:32.472208

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e24c8daeb39f'
down_revision = 'd2a8ee483146'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reply_to_user_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(None, 'users', ['reply_to_user_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('comments', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('reply_to_user_id')

    # ### end Alembic commands ###

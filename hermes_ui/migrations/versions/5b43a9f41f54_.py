"""empty message

Revision ID: 5b43a9f41f54
Revises: c3bd7511b28b
Create Date: 2019-07-19 16:13:19.563992

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5b43a9f41f54'
down_revision = 'c3bd7511b28b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recherche_interet', sa.Column('focus_cle', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('recherche_interet', 'focus_cle')
    # ### end Alembic commands ###

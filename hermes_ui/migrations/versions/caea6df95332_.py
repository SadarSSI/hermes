"""empty message

Revision ID: caea6df95332
Revises: 5b43a9f41f54
Create Date: 2019-08-06 10:08:49.314758

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'caea6df95332'
down_revision = '5b43a9f41f54'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('expression_reguliere_recherche_interet',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('expression_reguliere', sa.String(length=255), nullable=False),
    sa.ForeignKeyConstraint(['id'], ['recherche_interet.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.alter_column('action_noeud', 'createur_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('action_noeud', 'responsable_derniere_modification_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('automate', 'createur_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('automate', 'responsable_derniere_modification_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('detecteur', 'createur_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('detecteur', 'responsable_derniere_modification_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('recherche_interet', 'createur_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('recherche_interet', 'responsable_derniere_modification_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('recherche_interet', 'responsable_derniere_modification_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('recherche_interet', 'createur_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('detecteur', 'responsable_derniere_modification_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('detecteur', 'createur_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('automate', 'responsable_derniere_modification_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('automate', 'createur_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('action_noeud', 'responsable_derniere_modification_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('action_noeud', 'createur_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_table('expression_reguliere_recherche_interet')
    # ### end Alembic commands ###

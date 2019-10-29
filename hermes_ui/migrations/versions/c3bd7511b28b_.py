"""empty message

Revision ID: c3bd7511b28b
Revises: bbae7fae74c2
Create Date: 2019-07-19 14:26:56.055760

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3bd7511b28b'
down_revision = 'bbae7fae74c2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('requete_sql_action_noeud',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hote_type_protocol', sa.Enum('mysql', 'posgres', 'mariadb', 'mssql', 'oracle'), nullable=False),
    sa.Column('hote_ipv4', sa.String(), nullable=False),
    sa.Column('hote_port', sa.String(), nullable=False),
    sa.Column('hote_database', sa.String(), nullable=False),
    sa.Column('requete_sql', sa.Text(), nullable=False),
    sa.Column('nom_utilisateur', sa.String(), nullable=True),
    sa.Column('mot_de_passe', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['id'], ['action_noeud.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # op.alter_column('localisation_expression_recherche_interet', 'expression_droite',
    #            existing_type=sa.VARCHAR(),
    #            nullable=True)
    # op.alter_column('localisation_expression_recherche_interet', 'expression_gauche',
    #            existing_type=sa.VARCHAR(),
    #            nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.alter_column('localisation_expression_recherche_interet', 'expression_gauche',
    #            existing_type=sa.VARCHAR(),
    #            nullable=False)
    # op.alter_column('localisation_expression_recherche_interet', 'expression_droite',
    #            existing_type=sa.VARCHAR(),
    #            nullable=False)
    op.drop_table('requete_sql_action_noeud')
    # ### end Alembic commands ###
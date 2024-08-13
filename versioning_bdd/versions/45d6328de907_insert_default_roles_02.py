"""Insert default roles-02

Revision ID: 45d6328de907
Revises: 
Create Date: 2024-08-07 21:40:56.789123

"""
from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision = '45d6328de907'
down_revision = 'df1b87931758'
branch_labels = None
depends_on = None

# Configuration du context de hachage
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Le mot de passe en clair pour le super utilisateur
password = "admin"

# Hacher le mot de passe
hashed_password = pwd_context.hash(password)

def upgrade():
    # Insert default roles
    op.execute(
        sa.text(
            """
            INSERT INTO roles (role_id, role_name, description, author_get_doc, author_post_doc, author_put_doc, author_patch_doc, author_delete_doc, author_get_collection, author_post_collection, author_put_collection, author_patch_collection, author_delete_collection, author_get_user, author_post_user, author_put_user, author_patch_user, author_delete_user) VALUES
            (1, 'administrator', 'Administrateur, gére les utilisateurs', true, true, true, true, true, true, true, true, true, true, true, true, true, true),
            (2, 'projectManager', 'Chef de projet, gére les collections', true, true, true, true, true, true, true, true, true, true, true, false, false, false, false),
            (3, 'user', 'Utilisateur standard, ne gére que les documents', true, true, true, true, true, true, false, false, false, false, true, false, false, false, false)
            """
        )
    )

    # Insert super user
    op.execute(
        sa.text(
            """
            INSERT INTO users (user_id, username, passwords, email, role_id, date_de_creation, created_at) VALUES
            (1, 'admin', :hashed_password, 'admin@example.com', 1, CURRENT_DATE, CURRENT_TIMESTAMP)
            """
        ),
        {"hashed_password": hashed_password}
    )

def downgrade():
    # Delete super user
    op.execute(
        sa.text(
            """
            DELETE FROM users WHERE username='admin'
            """
        )
    )
    # Delete default roles
    op.execute(
        sa.text(
            """
            DELETE FROM roles WHERE role_name IN ('administrator', 'projectManager', 'user')
            """
        )
    )

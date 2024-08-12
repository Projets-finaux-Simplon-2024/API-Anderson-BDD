from passlib.context import CryptContext

# Initialiser le contexte de cryptage avec bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Mot de passe à hacher
super_password = "superuser"

# Hacher le mot de passe
hashed_password = pwd_context.hash(super_password)

# Afficher le mot de passe haché
print(hashed_password)

import os

SECRET_KEY = os.urandom(32).hex()  # Pour HS256, 32 octets
print(SECRET_KEY)

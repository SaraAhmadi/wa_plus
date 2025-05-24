from passlib.context import CryptContext

# Use bcrypt as the hashing algorithm
# Other schemes can be added for deprecation if needed, e.g., "sha256_crypt"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# For password hashing and verification
class Hasher:
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a plain password against a hashed password.
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """
        Hashes a plain password.
        """
        return pwd_context.hash(password)

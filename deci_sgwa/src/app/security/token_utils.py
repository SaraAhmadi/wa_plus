from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import settings # We will create this file next
from app.schemas.token import TokenData # Assuming TokenData schema is in app/schemas/token.py

ALGORITHM = settings.JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


# For JWT access token creation and decoding.
def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.

    :param subject: The subject of the token (e.g., user's email or ID).
    :param expires_delta: Optional timedelta for token expiration. If None, uses default.
    :return: The encoded JWT access token.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {"exp": expire, "sub": str(subject)}
    # You can add more claims to the token payload here if needed
    # e.g., "user_id": user_id, "roles": [role.name for role in user.roles]
    # Ensure these additional claims are also part of your TokenData schema if you plan to validate them

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decodes a JWT access token and validates its structure using TokenData schema.

    :param token: The JWT token string.
    :return: TokenData object if the token is valid and decodable, None otherwise.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        # Validate expiration
        expire_timestamp = payload.get("exp")
        if expire_timestamp is None or datetime.fromtimestamp(expire_timestamp, timezone.utc) < datetime.now(timezone.utc):
            # print("Token has expired") # For debugging
            return None # Token expired

        # Attempt to parse the subject into TokenData
        # This assumes 'sub' directly maps to 'email' or another primary field in TokenData
        # If 'sub' is user_id, and TokenData expects user_id, adjust accordingly
        # For simplicity, if 'sub' is email:
        token_data = TokenData(email=payload.get("sub"))
        # If you have more claims in the token and in TokenData, they would be validated here.
        # For example, if TokenData was: class TokenData(BaseModel): user_id: int; email: str
        # Then you would do: token_data = TokenData(**payload) after ensuring all keys exist

        return token_data
    except JWTError as e:
        # print(f"JWTError during token decoding: {e}") # For debugging
        return None
    except ValidationError as e:
        # print(f"ValidationError during token data parsing: {e}") # For debugging
        return None
    except Exception as e:
        # print(f"Unexpected error during token decoding: {e}") # For debugging
        return None


# Example usage (for testing or in services):
if __name__ == "__main__":
    # This requires settings to be available
    # Dummy settings for testing this script directly
    class DummySettings:
        SECRET_KEY = "your-very-secret-key-for-testing-only-do-not-use-in-prod"
        JWT_ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30

    settings = DummySettings()
    ALGORITHM = settings.JWT_ALGORITHM # Re-assign for local scope test
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    test_subject = "testuser@example.com"
    # Test token creation
    token = create_access_token(subject=test_subject)
    print(f"Generated Token: {token}")

    # Test token decoding
    decoded_payload = decode_access_token(token)
    if decoded_payload:
        print(f"Decoded Payload (TokenData): {decoded_payload}")
        print(f"Decoded Subject (email): {decoded_payload.email}")
    else:
        print("Token decoding failed or token is invalid/expired.")

    # Test expired token
    expired_token = create_access_token(subject=test_subject, expires_delta=timedelta(seconds=-1))
    decoded_expired_payload = decode_access_token(expired_token)
    if decoded_expired_payload:
        print(f"Decoded Expired Payload (should not happen): {decoded_expired_payload}")
    else:
        print("Expired token correctly identified as invalid.")

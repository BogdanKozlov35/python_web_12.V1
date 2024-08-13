from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Generates a hashed password using bcrypt.

    :param password: The plain text password to hash.
    :type password: str
    :return: The hashed password.
    :rtype: str
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if the provided plain password matches the hashed password.

    :param plain_password: The plain text password to verify.
    :type plain_password: str
    :param hashed_password: The hashed password to check against.
    :type hashed_password: str
    :return: True if the plain password matches the hashed password, False otherwise.
    :rtype: bool
    """
    return pwd_context.verify(plain_password, hashed_password)

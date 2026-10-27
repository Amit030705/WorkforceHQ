import argparse
import getpass
import sys

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an administrator account using a private password prompt.")
    parser.add_argument("--email", required=True, help="Administrator's email address")
    args = parser.parse_args()
    try:
        email = str(TypeAdapter(EmailStr).validate_python(args.email)).lower()
    except ValidationError:
        parser.error("Enter a valid email address.")
    password = getpass.getpass("New administrator password (at least 12 characters): ")
    confirmation = getpass.getpass("Confirm password: ")
    if len(password) < 12:
        parser.error("The password must contain at least 12 characters.")
    if password != confirmation:
        parser.error("The passwords do not match.")

    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.email == email)) is not None:
            parser.error("An account with that email address already exists.")
        db.add(User(email=email, password_hash=hash_password(password), role="admin"))
        db.commit()
    print(f"Administrator account created for {email}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


DEMO_USERS = [
    ("admin@demo.com", "Admin", "Admin1234!"),
    ("jane@demo.com", "Jane Smith", "Jane1234!"),
    ("bob@demo.com", "Bob Chen", "Bob1234!"),
]


async def main() -> None:
    async with SessionLocal() as db:
        for email, display_name, password in DEMO_USERS:
            existing = await db.scalar(select(User).where(User.email == email))
            if existing:
                if existing.display_name != display_name:
                    existing.display_name = display_name
                if not existing.password_hash:
                    existing.password_hash = hash_password(password)
            else:
                db.add(
                    User(
                        email=email,
                        display_name=display_name,
                        password_hash=hash_password(password),
                        is_active=True,
                    )
                )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())

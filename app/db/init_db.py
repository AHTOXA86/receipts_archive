import asyncio
from sqlmodel import Session
from .database import engine, init_db
from ..core.security import get_password_hash
from ..models import User

async def create_first_superuser():
    init_db()
    
    with Session(engine) as session:
        # Check if superuser already exists
        user = session.query(User).filter(User.email == "admin@example.com").first()
        if not user:
            user = User(
                username="admin",
                email="admin@example.com",
                full_name="Administrator",
                hashed_password=get_password_hash("admin"),
                disabled=False,
            )
            session.add(user)
            session.commit()
            print("Superuser created successfully!")
        else:
            print("Superuser already exists")

if __name__ == "__main__":
    asyncio.run(create_first_superuser()) 
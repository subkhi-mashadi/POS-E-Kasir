from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.public.user import User
from app.core.security import verify_password, create_access_token, create_refresh_token

async def authenticate_user(db: AsyncSession, email: str, password: str):
    result = await db.execute(select(User).where(User.email == email, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user

def generate_tokens(user: User) -> dict:
    return {
        "access_token": create_access_token({"sub": str(user.id), "role": user.role}),
        "refresh_token": create_refresh_token({"sub": str(user.id)}),
        "token_type": "bearer",
    }

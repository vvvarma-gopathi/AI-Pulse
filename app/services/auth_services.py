from requests import session
from typing import Annotated
from app.models.auth_model import Users
from app.schemas.auth_schemas import MessageResponse, UserRegister,UserLogin
from sqlalchemy import select
from fastapi import HTTPException,status,Depends
from fastapi.security import OAuth2PasswordBearer
from app.core.database import get_db
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError,PyJWTError
from datetime import datetime,timedelta
from app.core.config import settings

hash_password=PasswordHash.recommended()

def password_hash(password):
    hashed_password=hash_password.hash(password)
    return hashed_password

def create_jwt_token(user_email):
    expiration_time=datetime.utcnow()+timedelta(hours=int(settings.ExpirationTime))
    payload={
        "sub":user_email,
        "exp":expiration_time
    }
    return jwt.encode(payload=payload,key=settings.JwtSecretKey,algorithm=settings.HashAlgorithm)

OAuth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token:Annotated[str,Depends(OAuth2_scheme)],db:Annotated[session,Depends(get_db)]):
    try:
        payload=jwt.decode(token,key=settings.JwtSecretKey,algorithms=[settings.HashAlgorithm])
        email=payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
        user=db.scalar(select(Users).where(Users.email==email))
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
        return user
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")



async def add_user(user_data:UserRegister,db):
    if not db:
        return MessageResponse(message="Database connection error")
    email=user_data.email.strip().lower()
    if not email or '@' not in email:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail="email is not correct re enter the email to continue..")
    user=db.scalar(select(Users).where(Users.email==user_data.email))
    if user:
        raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED,detail="user already registered with the email..")
    user_details=user_data.model_dump()
    users_name=db.scalar(select(Users).where(Users.user_name==user_details['user_name']))
    if users_name:
        return HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED,detail=f"user name {user_details['user_name']} existed use another one.")
    user_details['password']=password_hash(user_details['password'])
    db.add(Users(**user_details))
    db.commit()
    return MessageResponse(message="user registration successfull.")

async def authenticate_user(user_credentials:UserLogin,db):
    if not db:
        return MessageResponse(message="Database connection error")
    email=user_credentials.email.strip().lower()
    if not email or '@' not in email:
        raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE,detail="email is not correct re enter the email to continue..")
    user=db.scalar(select(Users).where(Users.email==email))
    unautherised=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="email or password is incorrect!")
    if not user:
        raise unautherised
    if not hash_password.verify(user_credentials.password,user.password):
        raise unautherised
    token=create_jwt_token(user_credentials.email)
    return {"access_token":token,"token_type":"bearer"}


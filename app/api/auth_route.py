from fastapi import APIRouter,Depends,HTTPException,status
from schemas.auth_schemas import MessageResponse,UserRegister,UserLogin,JWTResponse
from core.database import get_db
from services import auth_services

auth_app=APIRouter(prefix='/auth',tags=['Authentication'])


@auth_app.post('/register',response_model=MessageResponse,status_code=status.HTTP_201_CREATED)
async def register_user(user_data:UserRegister,db=Depends(get_db)):
    return await auth_services.add_user(user_data,db)

@auth_app.post('/login',response_model=JWTResponse,status_code=status.HTTP_200_OK)
async def login_user(user_credentials:UserLogin,db=Depends(get_db)):
    return await auth_services.authenticate_user(user_credentials,db)
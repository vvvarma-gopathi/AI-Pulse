from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    user_name:str=Field(...,min_length=3,max_length=225)
    name:str=Field(...,min_length=4,max_length=225)
    email:str=Field(...,min_length=5,max_length=500,)
    password:str=Field(...,min_length=8,max_length=150)

class UserLogin(BaseModel):
    email:str=Field(...,min_length=6,max_length=500)
    password:str=Field(...,min_length=8,max_length=150)

class MessageResponse(BaseModel):
    message:str

class JWTResponse(BaseModel):
    access_token:str
    token_type:str="bearer"
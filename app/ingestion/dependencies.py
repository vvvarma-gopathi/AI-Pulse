from models.articles_model import Chat
from sqlalchemy.orm import Session

def create_chat_record(user_name:str,title:str,db:Session):
    existing_chat = db.query(Chat).filter(Chat.user_name == user_name, Chat.title == title).first()
    if existing_chat:
        return existing_chat

    new_chat = Chat(user_name=user_name,title=title)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)
    return new_chat

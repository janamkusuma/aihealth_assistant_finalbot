# app/schemas.py

from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    confirm_password: str

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        pw = info.data.get("password")
        if pw != v:
            raise ValueError("Passwords do not match")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True


class ChatCreateOut(BaseModel):
    id: int
    title: str


class ChatListOut(BaseModel):
    id: int
    title: str
    updated_at: str


class ChatRenameIn(BaseModel):
    title: str


class ChatSendIn(BaseModel):
    message: str
    language: Optional[str] = "en"  # ✅ selected language


class ChatSendOut(BaseModel):
    reply: str
    chat_title: str
    updated_at: str


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: str

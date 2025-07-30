from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, HttpUrl


class User(BaseModel):
    full_name: str
    email: EmailStr

class UserCreate(User):
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserUpdateOut(User):
    pass

class UserPasswords(BaseModel):
    old_password: str
    new_password: str

class UserOut(User):
    id: int
    urls_created: int
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str 
    jti: str

class TokenData(BaseModel):
    id: Optional[int] = None
    jti: Optional[str] = None

class UrlCreate(BaseModel):
    original: HttpUrl

class UrlInfo(BaseModel):
    id: int
    original: HttpUrl
    short_code: str
    clicks: int
    created_at: datetime

    class Config:
        from_attributes = True

class UrlOut(UrlInfo):
    short_url: HttpUrl

    class Config:
        from_attributes = True

class UrlUpdate(BaseModel):
    short_code: str

class ClickOut(BaseModel):
    ip_address: str
    timestamp: datetime
    class Config:
        from_attributes = True

class Analytics(BaseModel):
    url_id: int
    original: HttpUrl
    short_url: HttpUrl
    total_clicks: int
    click_details: List[ClickOut]

    class Config:
        from_attributes = True

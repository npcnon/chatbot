from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr
    first_name: str | None
    last_name: str | None
    model_config = ConfigDict(from_attributes=True)


class UserIn(UserBase):
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str
    
class UserOut(UserBase):
    id: UUID


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str

    @field_validator("old_password")
    @classmethod
    def old_password_is_not_blank(cls, value):
        if not value:
            raise ValueError("Old password field can't be blank!!!")
        return value

    @field_validator("new_password")
    @classmethod
    def new_password_is_not_blank(cls, value):
        if not value:
            raise ValueError("New password field can't be blank!!!")
        return value

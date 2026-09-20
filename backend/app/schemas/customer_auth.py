from pydantic import BaseModel, Field


class CustomerSignupRequest(BaseModel):
    login_id: str = Field(min_length=4, max_length=100)
    password: str = Field(min_length=4, max_length=100)
    user_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    phone: str | None = Field(default=None, max_length=30)


class CustomerLoginRequest(BaseModel):
    login_id: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=100)


class CustomerFindIdRequest(BaseModel):
    user_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=255)


class CustomerFindIdResponse(BaseModel):
    login_id: str


class CustomerResetPasswordRequest(BaseModel):
    login_id: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    new_password: str = Field(min_length=4, max_length=100)


class CustomerProfileUpdate(BaseModel):
    user_name: str = Field(min_length=1, max_length=100)
    email: str = Field(min_length=5, max_length=255)
    phone: str | None = Field(default=None, max_length=30)


class CustomerMessageResponse(BaseModel):
    message: str


class CustomerResponse(BaseModel):
    user_id: int
    login_id: str
    user_name: str
    email: str
    phone: str | None = None
    role_code: str = "BUYER"


class CustomerLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: CustomerResponse

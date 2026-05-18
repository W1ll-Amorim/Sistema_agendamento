from pydantic import BaseModel, EmailStr

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    confirmar_senha: str

class UsuarioResponse(BaseModel):
    id_usuario: str
    nome: str
    email: EmailStr

    class Config:
        from_attributes = True

class LoginSchema(BaseModel):
    email: EmailStr
    senha: str
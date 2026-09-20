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
    tipo: str  # 🔹 Adicionado para o frontend saber qual é o perfil do usuário

    class Config:
        # Nota: no Pydantic v2 from_attributes = True substituiu orm_mode = True
        from_attributes = True

class LoginSchema(BaseModel):
    email: EmailStr
    senha: str
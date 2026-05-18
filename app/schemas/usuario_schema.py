from pydantic import BaseModel, EmailStr

class UsuarioCreate(BaseModel):

    nome: str
    email: EmailStr
    senha: str
    confirmar_senha: str

class UsuarioResponse(BaseModel):
<<<<<<< HEAD
    id: int
=======
    id_usuario: str
>>>>>>> 90eb54dae882f9d8128c746bb2e118408616fb41
    nome: str
    email: EmailStr

    class Config:
        from_attributes = True

class LoginSchema(BaseModel):
    email: EmailStr
    senha: str
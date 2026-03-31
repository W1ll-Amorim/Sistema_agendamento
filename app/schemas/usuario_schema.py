from pydantic import BaseModel, EmailStr

class UsuarioCreate(BaseModel):

    nome: str
    email: EmailStr
    senha: str


class UsuárioResponde(BaseModel):
    id: int
    nome: str
    email: str

    class Config:
        orm_mode = True

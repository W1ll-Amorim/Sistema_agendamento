from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt

# 🔐 Configuração do hash de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔑 Configuração do JWT
SECRET_KEY = "sua_chave_secreta_aqui"  # ⚠️ depois coloque em variável de ambiente
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# =========================
# 🔹 HASH DE SENHA
# =========================

def hash_senha(senha: str) -> str:
    senha = senha[:72]
    return pwd_context.hash(senha)


def verificar_senha(senha: str, senha_hash: str) -> bool:
    senha = senha[:72]
    return pwd_context.verify(senha, senha_hash)


# =========================
# 🔹 TOKEN JWT
# =========================

def criar_token(data: dict):
    dados = data.copy()

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    dados.update({"exp": expire})

    token = jwt.encode(dados, SECRET_KEY, algorithm=ALGORITHM)

    return token


def verificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
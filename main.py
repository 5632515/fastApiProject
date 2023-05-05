import base64
import json
from datetime import datetime, timedelta
from typing import Union

import requests
import rsa
import uvicorn
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from fastapi import Depends, FastAPI, status, HTTPException
from fastapi.logger import logger
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

import pw
import pw2
import pw3
import pw4
import pw5

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}


def rsa_encrypt(message, public_key):
    rsa_key = RSA.importKey(public_key)
    cipher = PKCS1_v1_5.new(rsa_key)
    cipher_text = base64.b64encode(cipher.encrypt(message.encode(encoding="utf-8")))
    return cipher_text.decode()


public_key = "-----BEGIN PUBLIC KEY-----\nMFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBAK3XJwcCgwwuIswjV1PJRfDn6I85rL0d\nSqmgeoed3z4xz1nikdnZXbGrr5YXIlxRJnh3KpA6P8y70Z2ovC11O20CAwEAAQ==\n-----END PUBLIC KEY-----"
message = "KMcc$123456"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str


class Query(BaseModel):
    name: str
    ID: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

SERVER = "http://211.138.245.9:10010/dataServer"


def encrypt_for_backend(origin_text, public_key):
    pk = rsa.PublicKey.load_pkcs1(public_key.encode('utf-8'))


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def get_token(username, password):
    global public_key
    pw_encrypted = rsa_encrypt(password, public_key)
    api_url = SERVER + "/auth/loginWithoutVerify"
    data = {"username": username, "password": pw_encrypted}
    data_json = json.dumps(data)
    response = requests.post(api_url, data=data_json, headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ConnectionError(f'{api_url} status code is {response.status_code}.')
    response_load = json.loads(response.content)
    if not response_load['success']:
        error = response_load['code']
        raise ConnectionError(f'{api_url} status code is {error}.')
    return response_load['data']


def authenticate_user(fake_db, username: str, password: str):
    # user = get_user(fake_db, username)
    user = get_token(username, password)
    if not user:
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_info(origin_token):
    info_exception = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Could not get info may try again",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        info = requests.get(url=SERVER + "/auth/info", headers={'Authorization': origin_token})
        return json.loads(info.content)
    except:
        raise info_exception


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        origin_token: str = payload.get("sub")
        if origin_token is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # print('???')
    user = get_info(origin_token)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['token']}, expires_delta=access_token_expires
    )
    logger.log(msg='return token', level=1)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(current_user: User = Depends(get_current_active_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.post('/api/query')  # Item是json的校验
def create_item(user: Query, current_user: User = Depends(get_current_active_user)):  # 参数放在请求体内，传入JSON数据
    result = [pw.start(user.name, user.ID), pw2.start(user.name, user.ID), pw3.start(user.name, user.ID),
              pw4.start(user.name, user.ID), pw5.start(user.name, user.ID)]
    return result


# 启动主程序
if __name__ == '__main__':
    uvicorn.run(app='main:app', reload=True, host="0.0.0.0", port=7500)

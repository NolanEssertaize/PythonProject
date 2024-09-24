import hashlib
import jwt

from certifi import where
from fastapi import FastAPI, Request, Form, HTTPException, status, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jinja2.ext import loopcontrols
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Annotated, Union
from datetime import datetime, timedelta, timezone

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext

from sqlmodel import Field, Session, SQLModel, create_engine, select

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "ef1ab3a1bca055fc17dc21beedb8d36906d89ce51ec60a6516084c38395beba6"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

#Token


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    id: int
    username: str
    disabled: Union[bool, None] = None

class UserInDB(User):
    hashed_password: str

#DataBase
class Todousers(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    login: str
    password: str

class Todolist(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    id_user: int | None = Field(default=None, foreign_key="todousers.id")
    tag: str
    name: str
    description: str
    deadline: str
    createdtime: str
    bin: str

sqlite_file_name = "db/db.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
templates = Jinja2Templates(directory="templates")

#Automation Token

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(get_user_db(token_data.username), username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

#Automation
def get_user_db(login: str, password: str):
    with Session(engine) as session:
        statement = select(Todousers).where(Todousers.login == login)
        results = session.exec(statement).all()
        print(f"\nCommentaire {results[0]}\nFor username : {login}\n")
        user_info = results[0]
        hash_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        if not results:
            raise HTTPException(status_code=400, detail="User unknown")
        for user in results:
            if user.password != hash_password:
                raise HTTPException(status_code=400, detail="Incorrect password")
        else:
            return user_info

def updating_bin_status_with_id(user_id: int, id: int, changes: str) -> None:
    with Session(engine) as session:
        statement = select(Todolist).where(Todolist.id == id and Todolist.id_user == user_id)
        results = session.exec(statement)
        item = results.one()
        item.bin = changes
        session.commit()
        session.refresh(item)

def updating_description_with_id(id: int, changes: str) -> None:
    with Session(engine) as session:
        statement = select(Todolist).where(Todolist.id == id and Todolist.id_user == 1)
        results = session.exec(statement)
        item = results.one()
        item.description = changes
        session.commit()
        session.refresh(item)

def deleting_with_id(id: int) -> None:
    with Session(engine) as session:
        statement = select(Todolist).where(Todolist.id == id and Todolist.id_user == 1)
        results = session.exec(statement)
        item_db = results.first()
        session.delete(item_db)
        session.commit()

def updating_tag_with_id(user_id : int, id: int, changes: str) -> None:
    if changes != "":
        with Session(engine) as session:
            statement = select(Todolist).where(Todolist.id == id and Todolist.id_user == user_id)
            results = session.exec(statement)
            item = results.one()
            tag = ["Todo", "Doing", "Done"]
            if changes in tag:
                if item.tag == "Todo":
                    item.tag = "Doing"
                elif item.tag == "Doing":
                    item.tag = "Done"
                elif item.tag == "Done":
                    item.tag = "Todo"
            else:
                print("error")
            session.commit()
            session.refresh(item)

def checking_users(loginuser:str) -> bool:
    with Session(engine) as session:
        statement = select(Todousers).where(Todousers.login == loginuser)
        results = session.exec(statement)
        loginlist = []
        for login in results:
            loginlist.append(login)

        if loginuser in loginlist:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Name already taken",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            return True
#Route
@app.get("/")
async def home(request: Request, current_user: User = Depends(get_current_active_user)):
    with Session(engine) as session:
        statement = select(Todolist).where(Todolist.bin == "False" and Todolist.id_user == current_user.id)
        results = session.exec(statement)
        db = []
        for item in results:
            db.append(item)
    return templates.TemplateResponse("index.html", {"request": request, "db": db})

@app.get("/connexion")
async def connexion(request: Request):
    return templates.TemplateResponse("connexion.html", {"request": request})

@app.post("/token")
async def login_for_access_token(
    name: str = Form("name"),
    password: str = Form("password")
):
    user = get_user_db(name, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.login}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register")
async def add(name: str = Form("name"), password: str = Form("password")):
    hash_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
    new_user = Todousers(login= name, password=hash_password)
    with Session(engine) as session:
        session.add(new_user)
        session.commit()
    return RedirectResponse(url="/connexion", status_code=303)

@app.post("/add")
async def add(tag: str = Form("tag"), todo: str = Form("todo"), deadline: str = Form("deadline"), current_user: User = Depends(get_current_active_user)):
    new_item = Todolist(id_user= current_user.id, tag=tag, name=todo, deadline=deadline, createdtime=datetime.now().strftime("%Y-%m-%d"), bin="False")
    with Session(engine) as session:
        session.add(new_item)
        session.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/delete/{item_id}")
async def delete(item_id: int, current_user: User = Depends(get_current_active_user)):
    updating_bin_status_with_id(current_user.id, item_id, "True")
    return RedirectResponse(url="/", status_code=303)

@app.get("/bin")
async def show_bin(request: Request, current_user: User = Depends(get_current_active_user)):
    with Session(engine) as session:
        statement = select(Todolist).where(Todolist.bin == "True" and Todolist.id_user == current_user.id)
        results = session.exec(statement)
        db = []
        for item in results:
            db.append(item)
    return templates.TemplateResponse("bin.html", {"request": request, "db": db})

@app.get("/restaure/{item_id}")
async def restaure(item_id: int, current_user: User = Depends(get_current_active_user)):
    updating_bin_status_with_id(current_user.id, item_id, "False")
    return RedirectResponse(url="/", status_code=303)

@app.get("/deletetrash/{item_id}")
async def deletetrash(item_id: int, current_user: User = Depends(get_current_active_user)):
    deleting_with_id(current_user.id, item_id)
    return RedirectResponse(url="/bin", status_code=303)

@app.post("/edit/{item_id}")
async def edit(item_id: int, description: str = Form("description"), current_user: User = Depends(get_current_active_user)):
    updating_description_with_id(current_user.id, item_id, description)
    return RedirectResponse(url="/", status_code=303)

@app.get("/edit/{item_id}/{param}")
async def edit(item_id: int, param: str, current_user: User = Depends(get_current_active_user)):
    updating_tag_with_id(current_user.id, item_id, param)
    return RedirectResponse(url="/", status_code=303)
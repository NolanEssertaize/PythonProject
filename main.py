import hashlib
import jwt

from certifi import where
from fastapi import FastAPI, Request, Form, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jinja2.ext import loopcontrols
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Annotated, Union

from markdown_it.rules_block import table
from sqlalchemy import result_tuple
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing_extensions import Buffer

#Token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    id: int
    username: str
    disabled: Union[bool, None] = None

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
app = FastAPI()
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
templates = Jinja2Templates(directory="templates")

#Automation
def updating_bin_status_with_id(id: int, changes: str) -> None:
    with Session(engine) as session:
        statement = select(Todolist).where(Todolist.id == id and Todolist.id_user == 1)
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

def updating_tag_with_id(id: int, changes: str) -> None:
    if changes != "":
        with Session(engine) as session:
            statement = select(Todolist).where(Todolist.id == id and Todolist.id_user == 1)
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
async def home(request: Request):
    with Session(engine) as session:
        statement = select(Todolist).where(Todolist.bin == "False")
        results = session.exec(statement)
        db = []
        for item in results:
            db.append(item)
    return templates.TemplateResponse("index.html", {"request": request, "db": db})

@app.get("/connexion")
async def connexion(request: Request):
    return templates.TemplateResponse("connexion.html", {"request": request})

@app.post("/login")
async def add(name: str = Form("username"), password: str = Form("password")):
    with Session(engine) as session:
        statement = select(Todousers).where(Todousers.login == name)
        results = session.exec(statement).all()
        print(f"\n Commentaire {results}\nFor username : {name}")
        hash_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
        user_info = []
        if not results:
            raise HTTPException(status_code=400, detail="User unknown")
        for user in results:
            user_info = user
            if user.password != hash_password:
                raise HTTPException(status_code=400, detail="Incorrect password")
        else:
            return {"access_token": user_info, "token_type": "bearer" }

@app.post("/register")
async def add(name: str = Form("name"), password: str = Form("password")):

    hash_password = hashlib.sha256(password.encode("utf-8")).hexdigest()
    new_user = Todousers(login= name, password=hash_password)
    with Session(engine) as session:
        session.add(new_user)
        session.commit()
    return RedirectResponse(url="/connexion", status_code=303)

@app.post("/add")
async def add(tag: str = Form("tag"), todo: str = Form("todo"), deadline: str = Form("deadline")):
    new_item = Todolist(id_user= 1, tag=tag, name=todo, deadline=deadline, createdtime=datetime.now().strftime("%Y-%m-%d"), bin="False")
    with Session(engine) as session:
        session.add(new_item)
        session.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/delete/{item_id}")
async def delete(item_id: int):
    updating_bin_status_with_id(item_id, "True")
    return RedirectResponse(url="/", status_code=303)

@app.get("/bin")
async def show_bin(request: Request):
    with Session(engine) as session:
        statement = select(Todolist).where(Todolist.bin == "True" and Todolist.id_user == 1)
        results = session.exec(statement)
        db = []
        for item in results:
            db.append(item)
    return templates.TemplateResponse("bin.html", {"request": request, "db": db})

@app.get("/restaure/{item_id}")
async def restaure(item_id: int):
    updating_bin_status_with_id(item_id, "False")
    return RedirectResponse(url="/", status_code=303)

@app.get("/deletetrash/{item_id}")
async def deletetrash(item_id: int):
    deleting_with_id(item_id)
    return RedirectResponse(url="/bin", status_code=303)

@app.post("/edit/{item_id}")
async def edit(item_id: int, description: str = Form("description")):
    updating_description_with_id(item_id, description)
    return RedirectResponse(url="/", status_code=303)

@app.get("/edit/{item_id}/{param}")
async def edit(item_id: int, param: str):
    updating_tag_with_id(item_id, param)
    return RedirectResponse(url="/", status_code=303)

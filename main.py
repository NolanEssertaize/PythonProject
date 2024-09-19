from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Optional
from sqlmodel import Field, Session, SQLModel, create_engine, select

#DataBase usage

class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tag: str
    nom: str
    description: str
    deadline: str
    createdtime: str
    bin: str

sqlite_file_name = "db.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

#DataBase usage
app = FastAPI()

app.mount("/templates", StaticFiles(directory="templates"), name="templates")

# Initialize templates
templates = Jinja2Templates(directory="templates")

class TodoList:
    def __init__(self, name: str, deadline: str):
        self.Name = name
        self.Date = datetime.now().strftime("%Y-%m-%d")
        self.Deadline = deadline

@app.get("/")
async def home(request: Request):
    with Session(engine) as session:
        statement = select(Item).where(Item.bin == "False")
        results = session.exec(statement)
        db = []
        for item in results:
            db.append(item)
    return templates.TemplateResponse("index.html", {"request": request, "db": db})

@app.post("/add")
async def add(tag: str = Form("tag"), todo: str = Form("todo"), deadline: str = Form("deadline")):
    new_item = Item(tag=tag, nom=todo, deadline=deadline, createdtime=datetime.now().strftime("%Y-%m-%d"), bin="False")
    with Session(engine) as session:
        session.add(new_item)
        session.commit()
    return RedirectResponse(url="/", status_code=303)

@app.get("/delete/{item_id}")
async def delete(item_id: int):
    with Session(engine) as session:
        statement = select(Item).where(Item.id == item_id)
        results = session.exec(statement)
        item = results.one()
        item.bin = "True"
        session.commit()
        session.refresh(item)
    return RedirectResponse(url="/", status_code=303)

@app.get("/bin")
async def show_bin(request: Request):
    with Session(engine) as session:
        statement = select(Item).where(Item.bin == "True")
        results = session.exec(statement)
        db = []
        for item in results:
            db.append(item)
    return templates.TemplateResponse("bin.html", {"request": request, "db": db})


@app.get("/restaure/{item_id}")
async def restaure(item_id: int):
    with Session(engine) as session:
        statement = select(Item).where(Item.id == item_id)
        results = session.exec(statement)
        item = results.one()
        item.bin = "False"
        session.commit()
        session.refresh(item)
    return RedirectResponse(url="/", status_code=303)

@app.get("/deletetrash/{item_id}")
async def deletetrash(item_id: int):
    with Session(engine) as session:
        statement = select(Item).where(Item.id == item_id)
        results = session.exec(statement)
        item_db = results.first()
        session.delete(item_db)
        session.commit()
    return RedirectResponse(url="/bin", status_code=303)


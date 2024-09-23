from fastapi import FastAPI, Request, Form, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import Annotated

from sqlmodel import Field, Session, SQLModel, create_engine, select

#DataBase
class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tag: str
    nom: str
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
        statement = select(Item).where(Item.id == id)
        results = session.exec(statement)
        item = results.one()
        item.bin = changes
        session.commit()
        session.refresh(item)

def updating_description_with_id(id: int, changes: str) -> None:
    with Session(engine) as session:
        statement = select(Item).where(Item.id == id)
        results = session.exec(statement)
        item = results.one()
        item.description = changes
        session.commit()
        session.refresh(item)

def deleting_with_id(id: int) -> None:
    with Session(engine) as session:
        statement = select(Item).where(Item.id == id)
        results = session.exec(statement)
        item_db = results.first()
        session.delete(item_db)
        session.commit()

def updating_tag_with_id(id: int, changes: str) -> None:
    if changes != "":
        with Session(engine) as session:
            statement = select(Item).where(Item.id == id)
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
#Route
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
    updating_bin_status_with_id(item_id, "True")
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

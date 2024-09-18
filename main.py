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
    tag: str | None = Field(default=None)
    nom: str | None = Field(default=None)
    description: str | None = Field(default=None)
    deadline: str | None = Field(default=None)
    createdtime: str | None = Field(default=None)

sqlite_file_name = "db.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def select_item():
    with Session(engine) as session:
        statement = select(Item)
        results = session.execute(statement)
        return results

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

# Simulating a database with a list
todo_list = []

# Simulating a bin
bin_list = []

@app.get("/")
async def home(request: Request):
    results = select_item()
    return templates.TemplateResponse("index.html", {"request": request, "todo_list": todo_list, "results": results})

@app.post("/add")
async def add(todo: str = Form("todo"), deadline: str = Form("deadline")):
    new_item = TodoList(todo, deadline)
    todo_list.append(new_item)
    return RedirectResponse(url="/", status_code=303)

@app.get("/delete/{todo_id}")
async def delete(todo_id: int):
    if 0 <= todo_id < len(todo_list):
        bin_list.append(todo_list[todo_id])
        del todo_list[todo_id]
    return RedirectResponse(url="/", status_code=303)

@app.get("/bin")
async def show_bin(request: Request):
    return templates.TemplateResponse("bin.html", {"request": request, "bin_list": bin_list})

@app.get("/restaure/{bin_id}")
async def restaure(bin_id: int):
    if 0 <= bin_id < len(bin_list):
        todo_list.append(bin_list[bin_id])
        del bin_list[bin_id]
    return RedirectResponse(url="/", status_code=303)

@app.get("/deletetrash/{bin_id}")
async def deletetrash(bin_id: int):
    if 0 <= bin_id < len(bin_list):
        del bin_list[bin_id]
    return RedirectResponse(url="/bin", status_code=303)


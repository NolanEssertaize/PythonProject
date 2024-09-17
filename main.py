from fastapi import FastAPI, Request, Form, Depends
from fastapi.templating import Jinja2Templates
from datetime import datetime

app = FastAPI()

from fastapi.staticfiles import StaticFiles

app.mount("/templates", StaticFiles(directory="templates"), name="templates")

# Initialize templates
templates = Jinja2Templates(directory="templates")

class todolist:
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
    temporary_list = []
    i = len(temporary_list)
    for i in range(3):
        try:
            temporary_list.append(todo_list[i])
        except MemoryError:
            print("No more in the list")
    return templates.TemplateResponse("index.html", {"request": request, "todo_list": temporary_list})

@app.post("/add")
async def add(request: Request, todo: str = Form("todo"), deadline: str = Form("deadline")):
    new_item = todolist(todo, deadline)
    todo_list.append(new_item)
    return templates.TemplateResponse("index.html", {"request": request, "todo_list": todo_list})

@app.get("/delete/{todo_id}")
async def delete(request: Request, todo_id: int):
    if 0 <= todo_id < len(todo_list):
        bin_list.append(todo_list[todo_id])
        del todo_list[todo_id]
    return templates.TemplateResponse("index.html", {"request": request, "todo_list": todo_list})

@app.get("/restaure/{bin_id}")
async def restaure(request: Request, bin_id: int):
    if 0 <= bin_id < len(bin_list):
        todo_list.append(bin_list[bin_id])
        del bin_list[bin_id]
    return templates.TemplateResponse("index.html", {"request": request, "todo_list": todo_list})

@app.get("/deletetrash/{bin_id}")
async def deletetrash(request: Request, bin_id: int):
    if 0 <= bin_id < len(bin_list):
        del bin_list[bin_id]
    return templates.TemplateResponse("bin.html", {"request": request, "bin_list": bin_list})

@app.get("/bin")
async def show_bin(request: Request):
    return templates.TemplateResponse("bin.html", {"request": request, "bin_list": bin_list})
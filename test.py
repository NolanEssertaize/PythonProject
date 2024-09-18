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
        results = session.exec(select(Item)).all()
        print(f"\nResults : {results}\n")

select_item()

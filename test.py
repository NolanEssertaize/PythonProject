
from sqlmodel import Field, Session, SQLModel, create_engine, select

class Item(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    tag: str
    nom: str
    description: str
    deadline: str
    createdtime: str
    bin: bool

sqlite_file_name = "db.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, echo=True)

def test_bdd():
    with Session(engine) as session:
        statement = select(Item).where(Item.bin == "True")
        results = session.exec(statement)
        db = []
        for item in results:
            db.append(item)
            print("\n Item : ",item)

test_bdd()
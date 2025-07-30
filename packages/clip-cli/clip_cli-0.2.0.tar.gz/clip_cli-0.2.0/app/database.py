from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

#sqlalchemy url format
#'postgresql://<username>:<password>@<ip-address/hostname>/<databasename>

# SQLALCHEMY_DATABASE_URL = f'postgresql://{settings.database_username}:{settings.database_password}@{settings.database_hostname}/{settings.database_name}'

SQLALCHEMY_DATABASE_URL = f'{settings.database_url}'
engine = create_engine(SQLALCHEMY_DATABASE_URL)

print("connecting to", SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
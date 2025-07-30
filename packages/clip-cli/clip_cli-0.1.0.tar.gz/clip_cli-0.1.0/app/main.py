from typing import List
from fastapi import Depends, FastAPI
from .routers import user, auth, url
# from .scheduler import start_scheduler

#issues:
#1. fix token cleaning in db.

app = FastAPI()

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(url.router)

# @app.on_event("startup")
# def on_startup():
#     start_scheduler()



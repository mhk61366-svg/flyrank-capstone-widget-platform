from fastapi import FastAPI
from app.routes import widgets

app = FastAPI(title="Embedable Widget & Lead-Capture Platform")
app.include_router(widgets.router)



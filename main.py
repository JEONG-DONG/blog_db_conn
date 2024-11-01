from fastapi import FastAPI
from routes import blog, gpt

app = FastAPI()

# /blog => blog.router 연결
app.include_router(blog.router)

# /gpt => gpt.router 연결
app.include_router(gpt.router)
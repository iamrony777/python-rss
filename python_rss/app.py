from fastapi import FastAPI

# import uvicorn
from python_rss.routes import reddit

app = FastAPI()

app.include_router(router=reddit.router)

@app.get("/")
def root_ping():
    return {"hello": "from vercel"}


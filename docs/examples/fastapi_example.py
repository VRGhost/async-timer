import contextlib
import time

import uvicorn
from fastapi import FastAPI

import async_timer

DB_CACHE = {"initialised": False}


async def refresh_db():
    global DB_CACHE
    DB_CACHE |= {"initialised": True, "cur_value": time.time()}


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    async with async_timer.Timer(delay=5, target=refresh_db) as timer:
        await timer.wait(hit_count=1)  # block until the timer triggers at least once
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello World", "db_cache": DB_CACHE}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

from scale.fast_api import lifespan, get_scale
from fastapi import FastAPI

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.middleware("http")
async def scale_request(request, call_next):
    scale = get_scale()
    future = await scale.submit(call_next, None, request=request)
    return await future

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
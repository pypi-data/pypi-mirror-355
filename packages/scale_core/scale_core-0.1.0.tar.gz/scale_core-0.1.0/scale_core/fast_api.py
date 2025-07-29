from scales import Scale
from fastapi import FastAPI
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scale_instance
    
    scale_instance = Scale()
    
    yield
    
    scale_instance.stop()

def get_scale() -> Scale:
    """Получить экземпляр Scale"""
    if scale_instance is None:
        raise RuntimeError("Scale не инициализирован")
    return scale_instance
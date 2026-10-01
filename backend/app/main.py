from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.events import router as events_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version='0.1.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(events_router)


@app.get('/health')
def health_check() -> dict[str, str]:
    return {'status': 'ok', 'app': settings.app_name}


@app.get('/api/hello')
def hello() -> dict[str, str]:
    return {'message': 'Hello from FastAPI'}

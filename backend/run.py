"""Application entrypoint for uvicorn/ASGI serving.

Usage:
    uvicorn run:app --reload
"""

from app.main import create_app

app = create_app()

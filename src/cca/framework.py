"""Detect frameworks and libraries used in the project from import names."""
from __future__ import annotations

from cca.parser import FileInfo

_FRAMEWORK_MAP: dict[str, str] = {
    # web frameworks
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "starlette": "Starlette",
    "sanic": "Sanic",
    "aiohttp": "aiohttp",
    "tornado": "Tornado",
    "litestar": "Litestar",
    # data / ORM
    "sqlalchemy": "SQLAlchemy",
    "sqlmodel": "SQLModel",
    "tortoise": "Tortoise ORM",
    "peewee": "Peewee",
    "pymongo": "PyMongo",
    "motor": "Motor (async MongoDB)",
    "redis": "Redis",
    "elasticsearch": "Elasticsearch",
    # validation / serialization
    "pydantic": "Pydantic",
    "marshmallow": "Marshmallow",
    "attrs": "attrs",
    # task queues
    "celery": "Celery",
    "dramatiq": "Dramatiq",
    "rq": "RQ",
    "arq": "arq",
    # testing
    "pytest": "pytest",
    "unittest": "unittest",
    "hypothesis": "Hypothesis",
    # CLI
    "typer": "Typer",
    "click": "Click",
    "argparse": "argparse",
    # ML / data science
    "numpy": "NumPy",
    "pandas": "pandas",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "sklearn": "scikit-learn",
    "transformers": "HuggingFace Transformers",
    # HTTP clients
    "httpx": "HTTPX",
    "requests": "Requests",
    "aiohttp": "aiohttp",
    # auth
    "jose": "python-jose (JWT)",
    "jwt": "PyJWT",
    "passlib": "passlib",
    "bcrypt": "bcrypt",
    # cloud / infra
    "boto3": "AWS boto3",
    "google": "Google Cloud",
    "azure": "Azure SDK",
    # other common libs
    "rich": "Rich",
    "loguru": "Loguru",
    "structlog": "structlog",
    "alembic": "Alembic",
    "anyio": "AnyIO",
    "trio": "Trio",
}


def detect_frameworks(file_infos: list[FileInfo]) -> dict[str, str]:
    """Return {import_root: framework_label} for all detected frameworks."""
    all_imports: set[str] = set()
    for info in file_infos:
        for imp in info.imports:
            root = imp.split(".")[0]
            all_imports.add(root)

    detected: dict[str, str] = {}
    for root in all_imports:
        if root in _FRAMEWORK_MAP:
            detected[root] = _FRAMEWORK_MAP[root]

    return dict(sorted(detected.items(), key=lambda x: x[1]))

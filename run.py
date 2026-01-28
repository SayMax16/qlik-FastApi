"""Application entry point for running the Qlik Sense API server."""

import uvicorn

from src.api.core.config import settings


def main() -> None:
    """Run the FastAPI application with uvicorn."""
    uvicorn.run(
        "src.api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()

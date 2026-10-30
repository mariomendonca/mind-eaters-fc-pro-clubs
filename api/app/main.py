import asyncio
import contextlib
import logging
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app import queries
from app.collector import run_forever
from app.config import Settings, get_settings
from app.db import connect, init_schema
from app.ea import EASource, LiveEASource

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def create_app(settings: Optional[Settings] = None, source: Optional[EASource] = None) -> FastAPI:
    settings = settings or get_settings()

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        conn = connect(settings.db_path)
        init_schema(conn)
        conn.close()
        task = None
        if settings.collector_enabled:
            task = asyncio.create_task(run_forever(settings, source or LiveEASource(settings)))
        app.state.collector_task = task
        yield
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    app = FastAPI(title="Mind Eaters FC API", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")

    def db():
        conn = connect(settings.db_path)
        try:
            yield conn
        finally:
            conn.close()

    @app.get("/api/health")
    def health():
        # A stopped collector means history is silently lost: fail so Docker restarts us.
        task = getattr(app.state, "collector_task", None)
        if task is not None and task.done():
            return JSONResponse({"status": "collector stopped"}, status_code=503)
        return {"status": "ok"}

    @app.get("/api/status")
    def status(conn=Depends(db)):
        return queries.get_status(conn)

    @app.get("/api/overview")
    def overview(conn=Depends(db)):
        data = queries.get_overview(conn)
        if data is None:
            return JSONResponse({"detail": "no data yet"}, status_code=503)
        return data

    @app.get("/api/players")
    def players(conn=Depends(db)):
        return queries.list_players(conn)

    @app.get("/api/players/{gamertag}")
    def player(gamertag: str, conn=Depends(db)):
        data = queries.get_player(conn, gamertag)
        if data is None:
            raise HTTPException(404, "player not found")
        return data

    @app.get("/api/matches")
    def matches(limit: int = Query(50, ge=1, le=500), before: Optional[str] = None, conn=Depends(db)):
        return queries.list_matches(conn, limit, before)

    @app.get("/api/matches/{match_id}")
    def match(match_id: str, conn=Depends(db)):
        data = queries.get_match(conn, match_id)
        if data is None:
            raise HTTPException(404, "match not found")
        return data

    @app.get("/api/seasons")
    def seasons(conn=Depends(db)):
        return queries.get_seasons(conn)

    return app


app = create_app()

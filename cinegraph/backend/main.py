from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.routes import query, schema
from backend.services.neo4j_service import close_driver

app = FastAPI(title="CineGraph API")

# Allow Streamlit frontend running on default port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query.router, prefix="/api")
app.include_router(schema.router, prefix="/api")


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={"error": True, "detail": str(exc)},
    )


@app.on_event("shutdown")
async def shutdown():
    await close_driver()

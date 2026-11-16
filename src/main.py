import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.api.v1 import vexsGraphs, vexsHooksConnections, flowpipeNodes, vexsHooks
from src.core.logConfig import setup_logging
from src.flowpipeNodes.registry import discover_nodes

setup_logging()
log = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Discover nodes on application startup
    discover_nodes()
    yield

# Pass lifespan explicitly to app
app = FastAPI(title="VEXS API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vexsGraphs.router, prefix="/api/v1/vexsgraphs", tags=["VexsGraphs"])
app.include_router(flowpipeNodes.router, prefix="/api/v1/flowpipenodes", tags=["FlowpipeNodes"])
app.include_router(vexsHooksConnections.router, prefix="/api/v1/vexshooksconnections", tags=["VexsHooksConnections"])
app.include_router(vexsHooks.router, prefix="/api/v1/vexshooks", tags=["VexsHooks"])

@app.get("/")
def health_check():
    return {"status": "VEXS Backend running"}

# Correct path since main.py is already inside src/
nodes_path = Path(__file__).parent / "flowpipeNodes" / "nodes"
if nodes_path.exists(): app.mount("/static/nodes", StaticFiles(directory=str(nodes_path)), name="nodes")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.warning("%s %s -> 422: %s", request.method, request.url.path, exc.errors())
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# Log the detail of every HTTP error, uvicorn's access log only shows the status code
@app.exception_handler(StarletteHTTPException)
async def log_http_exception_handler(request: Request, exc: StarletteHTTPException):
    level = logging.ERROR if exc.status_code >= 500 else logging.WARNING
    log.log(level, "%s %s -> %d: %s", request.method, request.url.path, exc.status_code, exc.detail)
    return await http_exception_handler(request, exc)
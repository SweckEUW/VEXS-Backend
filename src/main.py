from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.flowpipe_nodes.registry import discover_nodes
from src.api.v1 import graphs, nodes

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

app.include_router(graphs.router, prefix="/api/v1/graphs", tags=["Graphs"])
app.include_router(nodes.router, prefix="/api/v1/nodes", tags=["Nodes"])

@app.get("/")
def health_check():
    return {"status": "VEXS Backend running"}

# Correct path since main.py is already inside src/
nodes_path = Path(__file__).parent / "flowpipe_nodes" / "nodes"
if nodes_path.exists(): app.mount("/static/nodes", StaticFiles(directory=str(nodes_path)), name="nodes")
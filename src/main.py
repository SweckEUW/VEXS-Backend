from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1 import graphs

app = FastAPI(title="VEXS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graphs.router, prefix="/api/v1/graphs", tags=["Graphs"])

@app.get("/")
def health_check():
    return {"status": "VEXS Backend running"}
import pathlib
from .workgraph import router as workgraph_router
from .scheduler import router as scheduler_router

__version__ = "0.1.0"

# static_dir points to plugin1/static
THIS_DIR = pathlib.Path(__file__).parent
static_dir = str(THIS_DIR / "static")

plugin = {
    "routers": {
        "workgraph": workgraph_router,
        "scheduler": scheduler_router,
    },
    "name": "WorkGraph",
    "static_dirs": {"workgraph": static_dir},
}

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict

class SerializedSubInputPlug(BaseModel):
    name: str  # full name "<parent>.<key>"
    value: Any = None
    connections: dict[str, str] = {}  # max. 1 entry: upstream identifier -> output name

class SerializedSubOutputPlug(BaseModel):
    name: str
    value: Any = None
    connections: dict[str, list[str]] = {}  # downstream identifier -> [input names]

class SerializedInputPlug(SerializedSubInputPlug):
    sub_plugs: dict[str, SerializedSubInputPlug] = {}  # keyed by "<key>"

class SerializedOutputPlug(SerializedSubOutputPlug):
    sub_plugs: dict[str, SerializedSubOutputPlug] = {}

class SerializedFlowpipeFunctionMeta(BaseModel):
    module: str
    name: str

class EditorNodeMetadata(BaseModel):
    id: str | None = None  # Baklava node id, keeps flowpipe identifiers stable
    type: str | None = None  # Baklava node type key
    position: dict[Literal["x", "y"], float] | None = None

class SerializedFlowpipeNodeMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    interpreter: str | None = None  # e.g. "python", "maya", "houdini", "nuke"
    batch_size: int | None = None
    label: str | None = None  # node title shown in the editor
    category: str | None = None  # node category shown in the editor
    editor: EditorNodeMetadata | None = None

class SerializedFlowpipeNode(BaseModel):
    module: str
    cls: str
    file_location: str | None = None
    name: str
    identifier: str
    inputs: dict[str, SerializedInputPlug] = {}
    outputs: dict[str, SerializedOutputPlug] = {}
    metadata: SerializedFlowpipeNodeMetadata = SerializedFlowpipeNodeMetadata()
    func: SerializedFlowpipeFunctionMeta | None = None  # only on FunctionNodes

class SerializedFlowpipeSubgraph(BaseModel):
    module: str
    cls: str
    name: str
    nodes: list[SerializedFlowpipeNode] = []

class SerializedFlowpipeGraph(SerializedFlowpipeSubgraph):
    subgraphs: list[SerializedFlowpipeSubgraph] = []  # only on the top level
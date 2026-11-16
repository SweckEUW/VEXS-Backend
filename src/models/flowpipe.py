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
    model_config = ConfigDict(extra="allow")  # editor-owned keys must survive a round-trip
    id: str | None = None  # Baklava node id, keeps flowpipe identifiers stable
    type: str | None = None  # Baklava node type key
    position: dict[Literal["x", "y"], float] | None = None
    width: float | None = None  # node width in px, None = Baklava default
    color: str | None = None  # CSS header color, set per node in the editor
    category: str | None = None  # sidebar group, "Uncategorized" if missing
    description: str | None = None  # shown in the sidebar and as tooltip
    icon: str | None = None  # image URL, rendered as <img src>
    local_values: dict[str, Any] | None = None  # own value of each input a graph input overrides, keyed by input key

class SerializedFlowpipeNodeMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")
    interpreter: str | None = None  # e.g. "python", "maya", "houdini", "nuke"
    batch_size: int | None = None  # fallback chunk size if the node has no "batch_size" input
    label: str | None = None  # node title shown in the editor
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

# Graph inputs are owned by the web editor: flowpipe neither writes nor reads them
GraphInputType = Literal["str", "int", "float", "bool"]

class SerializedGraphInputPlugRef(BaseModel):
    node: str  # identifier of the target node
    plug: str  # name of its input plug

class SerializedGraphInput(BaseModel):
    type: GraphInputType
    value: Any = None  # unset means no default, None is an explicit null default (check model_fields_set)
    description: str | None = None
    plugs: list[SerializedGraphInputPlugRef] = []

class EditorGraphInputsMetadata(BaseModel):
    position: dict[Literal["x", "y"], float] | None = None  # position of the Graph Inputs node

class EditorGraphView(BaseModel):
    panning: dict[Literal["x", "y"], float]
    scaling: float

class EditorGraphMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")  # editor-owned keys must survive a round-trip
    graph_inputs: EditorGraphInputsMetadata | None = None
    view: EditorGraphView | None = None  # canvas viewport, None keeps the current view on load

class SerializedFlowpipeGraph(SerializedFlowpipeSubgraph):
    subgraphs: list[SerializedFlowpipeSubgraph] = []  # only on the top level
    inputs: dict[str, SerializedGraphInput] = {}  # keyed by input name
    editor: EditorGraphMetadata | None = None  # owned by the web editor
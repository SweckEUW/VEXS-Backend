from flowpipe import INode, InputPlug, OutputPlug
from src.flowpipeNodes.registry import register_node

@register_node("nuke.render_node")
class NukeRenderNode(INode):
    def __init__(self, **kwargs):
        super(NukeRenderNode, self).__init__(**kwargs)
        InputPlug("script_path", self)
        OutputPlug("rendered_frames", self)

    def compute(self, script_path):
        # Render logic here
        return {"rendered_frames": "/path/to/frames"}
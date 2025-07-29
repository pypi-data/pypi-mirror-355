import typing as t

from common_py.workflow.nodes.node import NodeOutputData
from common_py.workflow.nodes.tools.human_feedback import (
    HumanFeedbackTool as HumanFeedbackInternal,
)
from common_py.workflow.nodes.tools.human_feedback import HumanFeedbackToolInput


def HumanFeedbackTool(**kwargs: t.Any) -> NodeOutputData:
    """
    This tool reads content from a worksheet by ID.
    """
    input = HumanFeedbackToolInput(**kwargs)
    tool = HumanFeedbackInternal(node_input_data=input)
    return tool.execute()

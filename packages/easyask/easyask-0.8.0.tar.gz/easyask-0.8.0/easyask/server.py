import logging
from typing import Any, List, Dict

from mcp.server import FastMCP

from easyask.logging_config import LOGGING_CONFIG
from easyask.settings import get_settings
from easyask.tools import chart

logging.config.dictConfig(LOGGING_CONFIG)
settings = get_settings()
mcp = FastMCP(name="easy-ask-tools", host=settings.host, port=settings.port)


@mcp.tool(
    name="get_chart_options",
    description="based on the dataset, generate chart options using the specified generator class",
)
def get_chart_options(dataset: List[List[Any]], dimensions: List[str]) -> Dict:
    return chart.get_chart_options(dataset, dimensions, config={"dashscope_api_key": settings.dashscope_api_key})


def serve():
    mcp.run(transport='sse')

from typing import Any, List, Type, Dict

from easyask.infras.chart.chart import Chart
from easyask.infras.chart.echarts import Echarts


def get_chart_options(dataset: List[List[Any]], dimensions: List[str], generator_cls: Type[Chart] = Echarts,
                      config: Dict = None):
    if config is None:
        config = {}

    generator = generator_cls(dataset, dimensions, config)
    return generator.get_options()

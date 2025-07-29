from typing import List, Any, Dict

from easyask.infras.chart.chart import Chart


class Echarts(Chart):
    def __init__(self, dataset: List[List[Any]], dimensions: List[str], config: Dict):
        super().__init__(dataset, dimensions, config)

        self.type = config.get("type", "bar")

    def get_options(self):
        if self.type == "bar":
            return BarEcharts(self.dataset, self.dimensions, self.config).get_options()

        if self.type == "line":
            return LineEcharts(self.dataset, self.dimensions, self.config).get_options()

        if self.type == "pie":
            return PieEcharts(self.dataset, self.dimensions, self.config).get_options()


class BarEcharts(Chart):
    def __init__(self, dataset: List[List[Any]], dimensions: List[str], config: Dict):
        super().__init__(dataset, dimensions, config)
        self.type = "bar"

    def get_options(self):
        return {
            "dataset": {
                "dimensions": self.dimensions,
                "source": self.dataset
            },
            "xAxis": {"type": "category"},
            "yAxis": {},
            "series": [{
                "name": dimension,
                "type": self.type,
                "barGap": 0,
                "encode": {"x": self.dimensions[0], "y": dimension, "tooltip": [dimension]}
            } for dimension in self.dimensions[1:]]
        }


class LineEcharts(Chart):
    def __init__(self, dataset: List[List[Any]], dimensions: List[str], config: Dict):
        super().__init__(dataset, dimensions, config)
        self.type = "line"

    def get_options(self):
        return {
            "dataset": {
                "dimensions": self.dimensions,
                "source": self.dataset
            },
            "xAxis": {},
            "yAxis": {},
            "series": [{
                "name": dimension,
                "type": self.type,
                "barGap": 0,
                "encode": {"x": self.dimensions[0], "y": dimension, "tooltip": [dimension]}
            } for dimension in self.dimensions[1:]]
        }


class PieEcharts(Chart):
    def __init__(self, dataset: List[List[Any]], dimensions: List[str], config: Dict):
        super().__init__(dataset, dimensions, config)
        self.type = "pie"

    def get_options(self):
        return {
            "tooltip": {},
            "legend": {
                "orient": "vertical",
                "left": "left"
            },
            "dataset": {
                "dimensions": self.dimensions,
                "source": self.dataset
            },
            "xAxis": {},
            "yAxis": {},
            "series": [{
                "name": dimension,
                "type": self.type,
                "barGap": 0,
                "radius": '50%',
                "encode": {"value": dimension, "itemName": self.dimensions[0]},
                "label": {
                    "show": True,
                    "formatter": f"{{b}}: {{@{dimension}}} ({{d}}%)"
                }
            } for dimension in self.dimensions[1:]]
        }

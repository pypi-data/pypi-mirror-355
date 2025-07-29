import json
import logging
from typing import List, Any, Dict

import dashscope

from easyask.infras.chart.chart import Chart

logger = logging.getLogger(__name__)

initial_prompt = """
You are a echarts expert.
Please help to generate a echarts options. Your response should ONLY be based on the given context and follow the response guidelines and format instructions. 
"""

documentation_prompt = """
===Documentation
Dataset is a component dedicated to manage data. The ideas of data visualization: (I) Provide the data, (II)Mapping from data to visual to become a chart.
In short, you can set these configs of mapping:
    * Specify 'column' or 'row' of dataset to map the series. You can use series.seriesLayoutBy to configure it. The default is to map according to the column.
    * Rule of specifying dimension mapping: how to mapping from dimensions of 'dataset' to axis, tooltip, label and visualMap. To configure the mapping, please use series.encode and visualMap. The previous case did not give the mapping configuration so that ECharts will follow the default: if x-axis is category, mapping to the first row in dataset.source; three-column chart mapping with each row in dataset.source one by one.

Having the dataset, you can configure flexibly how the data map to the axis and series.
You can use seriesLayoutBy to change the understanding of row and column of the chart. seriesLayoutBy can be:
    * 'column': Default value. The series are placed above the column of dataset.
    * 'row': The series are placed above the row of dataset.

Most of the data described in commonly used charts is a "two-dimensional table" structure, in the previous case, we use a 2D array to contain a two-dimensional table. Now, when we map a series to a column, that column was called a "dimension" and each row was called "item", vice versa.
The dimension can have their name to display in the chart. Dimension name can be defined in the first column (row). ECharts will automatically check if the first column (row) contained dimension name in dataset.source. You can also use dataset.sourceHeader: true to declare that the first column (row) represents the dimension name.
After understand the concept of dimension, you can use series.encode to make a mapping:

Examples:
```javascript
var option = {
  dataset: {
    source: [
      ['score', 'amount', 'product'],
      [89.3, 58212, 'Matcha Latte'],
      [57.1, 78254, 'Milk Tea'],
    ]
  },
  xAxis: {},
  yAxis: { type: 'category' },
  series: [
    {
      type: 'bar',
      encode: {
        // Map "amount" column to x-axis.
        x: 'amount',
        // Map "product" row to y-axis.
        y: 'product'
      }
    }
  ]
};
```

The basic structure of series.encode declaration:
    To the left of the colon: Specific name of axis or label.
    To the right of the colon: Dimension name (string) or number(int, count from 0), to specify one or several dimensions (using array).
Generally, the following info is not necessary to be defined. Fill in as needed.
```javascript
// Supported in every coordinate and series:
encode: {
  // Display the value of dimension named "product" and "score" in tooltip.
  tooltip: ['product', 'score']
  // Connect dimension name of "Dimension 1" and "Dimension 3" as the series name. (Avoid to repeat longer names in series.name)
  seriesName: [1, 3],
  // Means to use the value in "Dimension 2" as the id. It makes the new and old data correspond by id
	// when using setOption to update data, so that it can show animation properly.
  itemId: 2,
  // The itemName will show in the legend of Pie Charts.
  itemName: 3
}

// Grid/cartesian coordinate unique configs:
encode: {
  // Map "Dimension 1", "Dimension 5" and "dimension named 'score'" to x-axis:
  x: [1, 5, 'score'],
  // Map "Dimension 0" to y-axis:
  y: 0
}

// singleAxis unique configs:
encode: {
  single: 3
}

// Polar coordinate unique configs:
encode: {
  radius: 3,
  angle: 2
}

// Geo-coordinate unique configs:
encode: {
  lng: 3,
  lat: 2
}

// For some charts without coordinate like pie chart, funnel chart:
encode: {
  value: 3
}
```

"""

example_prompt = """
===Example
Example 1, Bar Chart:
```javascript
option = {
  legend: {},
  tooltip: {},
  dataset: {
    dimensions: ['product', '2015', '2016', '2017'],
    source: [
      ['Matcha Latte', 43.3, 85.8, 93.7],
      ['Milk Tea', 83.1, 73.4, 55.1],
    ]
  },
  xAxis: { type: 'category' },
  yAxis: {},
  series: [{
    name: '2015',
    type: 'bar',
    barGap: 0,
    encode: { x: 'product', y: '2015',  tooltip: ['2015']}
  },{
    name: '2016',
    type: 'bar',
    barGap: 0,
    encode: { x: 'product', y: '2016',  tooltip: ['2016']}
  }, {
    name: '2017',
    type: 'bar',
    barGap: 0,
    encode: { x: 'product', y: '2017',  tooltip: ['2017']}
  }]
};

Example 2, Line Chart:
```javascript
option = {
  legend: {},
  tooltip: {},
  dataset: {
    dimensions: ['day', 'v1', 'v2'],
    source: [
      [2, 85.8, 93.7],
      [3, 73.4, 55.1],
      [5, 73.4, 55.1],
    ]
  },
  xAxis: {},
  yAxis: {},
  series: [{
    name: 'v1',
    type: 'line',
    encode: { x: 'day', y: 'v1',  tooltip: ['v1']}
  },{
    name: 'v2',
    type: 'line',
    encode: { x: 'day', y: 'v2',  tooltip: ['v2']}
  }]
};

Example 3, Pie Chart:
```javascript
option = {
  tooltip: {},
  legend: {
    orient: 'vertical',
    left: 'left'
  },
  dataset: {
    dimensions: ['provience', 'v1', 'v2'],
    source: [
      ['s1', 85.8, 93.7],
      ['s2', 73.4, 55.1],
      ['s3', 73.4, 55.1],
    ]
  },
  series: [{
    name: 'v1',
    type: 'pie',
    radius: '50%',
    center: ['25%', '25%'],
    encode: { value: 'v1', itemName: 'provience'},
    label: {
        show: true,
        formatter: '{b}: {@v1} ({d}%)'
      }
    },{
    name: 'v2',
    type: 'pie',
    radius: '50%',
    center: ['75%', '25%'],
    encode: { value: 'v2', itemName: 'provience'},
    label: {
        show: true,
        formatter: '{b}: {@v2} ({d}%)'
      }
    }
  ]
};

```

"""

instruction_prompt = """
===Response Guidelines
1. Response should ONLY be based on the given context and follow the response guidelines and format instructions.
2. Please think step by step and analyze the documentation and example carefully to ensure a full understanding of the context.
3. The response should be a valid echarts options object.
4. The response should start with prefix RESULT: and the reset should only contain valid JSON configs, no need to include options = `.
5. You should choose the proper chart type based on the dataset and dimensions provided. and you can also combine multiple chart types in one echarts options.
"""

user_prompt = """
===User Input
Given the dataset config as below:
```javascript
option = {{
  dataset: {{
    dimensions: {dimensions},
    source: {dataset}
  }},
}};
```
"""


class QwenEcharts(Chart):
    def __init__(self, dataset: List[List[Any]], dimensions: List[str], config: Dict):
        super().__init__(dataset, dimensions, config)

        self.api_key = config.get("dashscope_api_key", "")
        self.model = self.config.get("model", "qwen-max")

    def get_prompts(self):
        """
        Example:
        ```python
        chart.get_options_prompt()
        ```

        This method is used to generate a prompt for the LLM to generate echarts options.

        Args:

        Returns:
            any: The prompt for the LLM to generate echrats options.
        """

        return [{"role": "system",
                 "content": "\n".join([initial_prompt, documentation_prompt, example_prompt, instruction_prompt])},
                {"role": "user", "content": user_prompt.format(dimensions=json.dumps(self.dimensions),
                                                               dataset=json.dumps(self.dataset))}]

    def get_options(self):
        prompts = self.get_prompts()
        num_tokens = 0
        for message in prompts:
            num_tokens += len(message["content"]) / 4

        logger.info(f"Using llm {self.model} for {num_tokens} tokens (approx)")

        response = dashscope.Generation.call(
            api_key=self.api_key,
            model=self.model,
            messages=prompts,
            result_format='message'
        )

        for choice in response.output.choices:
            if "text" in choice:
                return choice.text

        result = response.output.choices[0].message.content

        simi_index = result.index(':')
        if simi_index == -1:
            raise ValueError(f"Invalid response format: {result}")

        result = result[simi_index + 1:].strip()
        try:
            json.loads(result)
            return result
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in response: {result}") from e

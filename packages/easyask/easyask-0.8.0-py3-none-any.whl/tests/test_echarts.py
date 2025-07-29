import json

import pytest

from easyask.tools import chart


@pytest.mark.skip(reason="This test is skipped since api key reason")
def test_qwen_echarts_options():
    options = chart.get_chart_options([
        ['Matcha Latte', 43.3, 85.8, 93.7],
        ['Milk Tea', 83.1, 73.4, 55.1],
        ['Cheese Cocoa', 86.4, 65.2, 82.5],
        ['Walnut Brownie', 72.4, 53.9, 39.1]
    ], ['product', '2015', '2016', '2017'])

    print(options)

    assert json.loads(options) is not None


def test_bar_echarts_options():
    options = chart.get_chart_options([
        ['Matcha Latte', 43.3, 85.8, 93.7],
        ['Milk Tea', 83.1, 73.4, 55.1],
        ['Cheese Cocoa', 86.4, 65.2, 82.5],
        ['Walnut Brownie', 72.4, 53.9, 39.1]
    ], ['product', '2015', '2016', '2017'], config={"type": "bar"})

    assert options == {'dataset': {'dimensions': ['product', '2015', '2016', '2017'],
                                   'source': [['Matcha Latte', 43.3, 85.8, 93.7],
                                              ['Milk Tea', 83.1, 73.4, 55.1],
                                              ['Cheese Cocoa', 86.4, 65.2, 82.5],
                                              ['Walnut Brownie', 72.4, 53.9, 39.1]]},
                       'series': [{'barGap': 0,
                                   'encode': {'tooltip': ['2015'], 'x': 'product', 'y': '2015'},
                                   'name': '2015',
                                   'type': 'bar'},
                                  {'barGap': 0,
                                   'encode': {'tooltip': ['2016'], 'x': 'product', 'y': '2016'},
                                   'name': '2016',
                                   'type': 'bar'},
                                  {'barGap': 0,
                                   'encode': {'tooltip': ['2017'], 'x': 'product', 'y': '2017'},
                                   'name': '2017',
                                   'type': 'bar'}],
                       'xAxis': {'type': 'category'},
                       'yAxis': {}}


def test_line_echarts_options():
    options = chart.get_chart_options([
        [1, 85.8, 93.7],
        [2, 73.4, 55.1],
        [3, 65.2, 82.5],
        [4, 53.9, 39.1]
    ], ['x', '2016', '2017'], config={"type": "line"})

    assert options == {'dataset': {'dimensions': ['x', '2016', '2017'],
                                   'source': [[1, 85.8, 93.7],
                                              [2, 73.4, 55.1],
                                              [3, 65.2, 82.5],
                                              [4, 53.9, 39.1]]},
                       'series': [{'barGap': 0,
                                   'encode': {'tooltip': ['2016'], 'x': 'x', 'y': '2016'},
                                   'name': '2016',
                                   'type': 'line'},
                                  {'barGap': 0,
                                   'encode': {'tooltip': ['2017'], 'x': 'x', 'y': '2017'},
                                   'name': '2017',
                                   'type': 'line'}],
                       'xAxis': {},
                       'yAxis': {}}


def test_pie_echarts_options():
    options = chart.get_chart_options([
        [1, 85.8],
        [2, 73.4],
        [3, 65.2],
        [4, 53.9]
    ], ['x', '2016'], config={"type": "pie"})

    assert options == {'dataset': {'dimensions': ['x', '2016'],
                                   'source': [[1, 85.8], [2, 73.4], [3, 65.2], [4, 53.9]]},
                       'legend': {'left': 'left', 'orient': 'vertical'},
                       'series': [{'barGap': 0,
                                   'encode': {'itemName': 'x', 'value': '2016'},
                                   'label': {'formatter': '{b}: {@2016} ({d}%)', 'show': True},
                                   'name': '2016',
                                   'radius': '50%',
                                   'type': 'pie'}],
                       'tooltip': {},
                       'xAxis': {},
                       'yAxis': {}}

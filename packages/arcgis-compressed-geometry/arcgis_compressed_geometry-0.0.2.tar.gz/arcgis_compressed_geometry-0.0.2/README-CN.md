# arcgis-compressed-geometry
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/arcgis-compressed-geometry.svg)](https://badge.fury.io/py/arcgis-compressed-geometry)
[![Tests](https://github.com/maslke/py_arcgis_compressed_geometry/actions/workflows/tests.yml/badge.svg)](https://github.com/maslke/py_arcgis_compressed_geometry/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/maslke/py_arcgis_compressed_geometry/branch/master/graph/badge.svg?token=8GWDG6CGQ0)](https://codecov.io/gh/maslke/py_arcgis_compressed_geometry)

一个用于编码和解码 ArcGIS 压缩几何格式的 Python 库。

## 简介

该库提供了 ArcGIS 压缩几何格式的编码和解码功能。支持以下坐标格式:

- xy (二维坐标)
- xyz (带高程的三维坐标)
- xym (带测量值的坐标)
- xyzm (带高程和测量值的坐标)

## 安装

可以通过如下指令通过pip来安装：

```shell
pip install arcgis-compressed-geometry==0.0.1
```


## 使用方法

### Encode

```python

from arcgis_compressed_geometry import encode

coordinates = [
        [-122.40645857695421, 37.78272915354862],
        [-122.40609876765315, 37.78299901052442],
        [-122.40597283439777, 37.78305298191958],
        [-122.40417378789242, 37.7844382477287],
    ]
    geometry = encode(coordinates, "xy", 55585)
    assert geometry == "+0+1+0+1m91-6fkfr+202tp+k+f+7+3+34+2d"
```

### Decode

```python

from arcgis_compressed_geometry import decode

points = decode(
        "+0+1+2+1m91-6733n+1pjfe+g-e+1b-r+9-9+c-h+2-j-3-v-7-j-b-m-5-7-e-f-1a-u-6-7-4-9-3-a-1-n+1-4j|+5rg+81s+7n+i0+4f+7r+7g+ce+7n+9j+3h+7n+ib+3a+3q+45+97+1qs"
    )

```

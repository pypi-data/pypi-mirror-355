from typing import TypedDict, Optional, List, Any, Literal

from typing_extensions import NotRequired

ItemType = Literal[
    "bar",
    "barpolar",
    "box",
    "candlestick",
    "carpet",
    "choropleth",
    "choroplethmapbox",
    "cone",
    "contour",
    "contourcarpet",
    "densitymapbox",
    "funnel",
    "funnelarea",
    "heatmap",
    "heatmapgl",
    "histogram",
    "histogram2d",
    "histogram2dcontour",
    "image",
    "indicator",
    "isosurface",
    "mesh3d",
    "ohlc",
    "parcats",
    "parcoords",
    "pie",
    "pointcloud",
    "sankey",
    "scatter",
    "scatter3d",
    "scattercarpet",
    "scattergeo",
    "scattergl",
    "scattermapbox",
    "scatterpolar",
    "scatterpolargl",
    "scatterternary",
    "splom",
    "streamtube",
    "sunburst",
    "surface",
    "table",
    "treemap",
    "violin",
    "volume",
    "waterfall",
]


class Item(TypedDict):
    name: str
    type: ItemType
    layout: NotRequired[dict]
    config: NotRequired[dict]
    traces: NotRequired[dict]
    groups: NotRequired[dict]
    filter: NotRequired[dict]
    transforms: NotRequired[dict]
    h: int
    w: int
    x: int
    y: NotRequired[int]


class Template(TypedDict):
    uuid: NotRequired[str]
    items: List[Item]
    tags: NotRequired[List[str]]
    name: Optional[str]


class Dataset(TypedDict):
    uuid: NotRequired[str]
    data: List[Any]
    tags: NotRequired[List[str]]
    name: Optional[str]

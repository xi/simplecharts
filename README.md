# Features

-   no external dependencies
-   produces clean SVG
-   available charts: grouped columns, stacked columns, lines, stacked
    areas

# Limitations

-   not interactive
-   not configurable
-   maximum of 6 colors
-   no wrapping for long labels

# Usage

```python
from simplecharts import StackedColumnRenderer

renderer = StackedColumnRenderer()
data = {
    'rows': [{
        'label': 'Apples',
        'values': [3, 2, 5],
    }, {
        'label': 'Oranges',
        'values': [4, 2, 3],
    }, {
        'label': 'Pears',
        'values': [4, 3, 4],
    }, {
        'label': 'Bananas',
        'values': [5, 1, 2],
    }],
    'legend': ['John', 'Jane', 'Joe'],
}
svg = renderer.render(data)
```

![example](https://github.com/xi/simplecharts/blob/main/tests/simple_StackedColumnRenderer.svg)

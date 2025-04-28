import argparse
import csv
import math
import sys
from xml.sax.saxutils import escape

COLORS = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33']


def round_max(value):
    if value <= 0:
        return 10
    tail = 10 ** math.floor(math.log(value, 10))
    head = int(value / tail) + 1
    if head & 1:
        head += 1
    return head * tail


class BaseRenderer:
    stacked = False

    def __init__(
        self, height=480, width=640, padding=5, colors=COLORS, ui_color='#333'
    ):
        self.height = height
        self.width = width
        self.padding = padding
        self.colors = colors
        self.ui_color = ui_color

        self.font_size = 16
        self.char_width = 10
        self.char_padding = 4
        self.x_labels = self.char_width * 5
        self.y_labels = 20
        self.y_legend = 20

    def get_color(self, i):
        return self.colors[i % len(self.colors)]

    def attrs(self, **kwargs):
        return ''.join(
            ' {}="{}"'.format(key.replace('_', '-'), escape(str(value)))
            for key, value in sorted(kwargs.items())
        )

    def element(self, tag, content=None, **attrs):
        if content:
            if '\n' in content:
                lines = content.strip().split('\n')
                content = '\n' + '\n'.join('\t' + l for l in lines) + '\n'
            return f'<{tag}{self.attrs(**attrs)}>{content}</{tag}>\n'
        else:
            return f'<{tag}{self.attrs(**attrs)} />\n'

    def line(self, x1, x2, y1, y2, color, **kwargs):
        return self.element(
            'line', x1=x1, x2=x2, y1=y1, y2=y2, stroke=color, **kwargs)

    def text(self, s, x, y, **kwargs):
        return self.element(
            'text', escape(str(s)), x=x, y=y, fill=self.ui_color, **kwargs)

    def rect(self, x, y, width, height, title=None, **kwargs):
        content = None
        if title:
            content = self.element('title', escape(str(title)))
        return self.element(
            'rect', content, x=x, y=y, width=width, height=height, **kwargs)

    def circle(self, x, y, radius=3, title=None, **kwargs):
        content = None
        if title:
            content = self.element('title', escape(str(title)))
        return self.element('circle', content, cx=x, cy=y, r=radius, **kwargs)

    def polyline(self, points, **kwargs):
        d = ' '.join('{:g},{:g}'.format(*p) for p in points)
        return self.element('polyline', points=d, **kwargs)

    def get_title(self, rows, legend, i, j):
        return rows[i]['values'][j]

    def render_axes(self, rows, max_value):
        s = ''
        s += self.line(0, 0, 0, self.height, self.ui_color)
        s += self.line(0, self.width, self.height, self.height, self.ui_color)

        if isinstance(max_value, float):
            half = max_value / 2
        else:
            half = max_value // 2

        group = ''
        for y, value in [
            (self.height, 0),
            (self.height / 2, half),
            (0, max_value),
        ]:
            group += self.text(value, -self.char_padding, y, **{
                'dominant-baseline': 'middle',
                'text-anchor': 'end',
            })
        s += self.element('g', group, **{
            'aria-hidden': 'true',
        })

        group = ''
        width = self.width / len(rows)
        y = self.height + self.y_labels / 2
        for i, row in enumerate(rows):
            x = (i + 0.5) * width
            group += self.text(row['label'], x, y, **{
                'dominant-baseline': 'middle',
                'text-anchor': 'middle',
                'role': 'columnheader',
            })
        s += self.element('g', group, role='row')

        return s

    def render_legend(self, legend):
        rows = [[]]
        width = 0
        max_width = 0
        for label in legend:
            w = (
                self.char_width + self.char_padding  # square
                + len(label) * self.char_width  # text
                + self.char_width  # margin
            )
            if width + w > self.width:
                rows.append([])
                width = 0
            rows[-1].append(label)
            width += w
            max_width = max(width, max_width)

        max_width += 2 * self.char_padding - self.char_width

        s = self.rect(
            self.width - max_width,
            -self.y_legend,
            max_width,
            self.y_legend * len(rows),
            fill='none',
            stroke=self.ui_color,
        )

        i = 0
        for j, row in enumerate(rows):
            x = self.width - max_width + self.char_padding
            y = (j - 0.5) * self.y_legend
            for label in row:
                # square
                size = self.char_width
                s += self.rect(x, y - size / 2, size, size, fill=self.get_color(i))
                x += self.char_width + self.char_padding
                # text
                s += self.text(label, x, y, **{
                    'dominant-baseline': 'middle',
                })
                x += len(label) * self.char_width
                # margin
                x += self.char_width
                i += 1

        return self.element('g', s, **{
            'aria-hidden': 'true',
        })

    def render_rows(self, rows, legend, max_value):
        raise NotImplementedError

    def get_view_box(self):
        p = 2 * self.padding
        x = -(self.padding + self.x_labels)
        y = -(self.padding + self.y_legend)
        width = self.width + p + self.x_labels
        height = self.height + p + self.y_labels + self.y_legend
        return f'{x:g} {y:g} {width:g} {height:g}'

    def render(self, data):
        if self.stacked:
            max_value = max(sum(row['values']) for row in data['rows'])
        else:
            max_value = max(max(row['values']) for row in data['rows'])
        max_value = round_max(max_value)

        legend = data.get('legend', [])
        content = ''
        content += self.render_axes(data['rows'], max_value)
        if legend:
            content += self.render_legend(legend)
        content += self.render_rows(data['rows'], legend, max_value)
        content = self.element('g', content, role='table')

        return self.element(
            'svg',
            content,
            xmlns='http://www.w3.org/2000/svg',
            viewBox=self.get_view_box(),
            **{
                'font-size': self.font_size,
                'font-family': 'sans-serif',
            },
        )


class ColumnRenderer(BaseRenderer):
    def render_rows(self, rows, legend, max_value):
        s = ''
        n = len(rows)
        k = len(rows[0]['values'])
        width = self.width / n / (k + 2)
        for j in range(k):
            group = ''
            for i in range(n):
                value = rows[i]['values'][j]
                height = self.height * value / max_value
                x = width * (i * (k + 2) + j + 1)
                group += self.rect(
                    x,
                    self.height - height - 1,
                    width,
                    height,
                    title=self.get_title(rows, legend, i, j),
                    role='cell',
                )
            s += self.element(
                'g', group, fill=self.get_color(j), stroke='white', role='row'
            )
        return s


class StackedColumnRenderer(BaseRenderer):
    stacked = True

    def render_rows(self, rows, legend, max_value):
        s = ''
        n = len(rows)
        k = len(rows[0]['values'])
        groups = ['' for j in range(k)]
        width = self.width / n
        for i, row in enumerate(rows):
            y = self.height - 1
            for j, value in enumerate(row['values']):
                height = self.height * value / max_value
                x = width * (i + 0.5)
                y -= height
                groups[j] += self.rect(
                    x - width / 6,
                    y,
                    width / 3,
                    height,
                    title=self.get_title(rows, legend, i, j),
                    role='cell',
                )
        for j, group in enumerate(groups):
            s += self.element(
                'g', group, fill=self.get_color(j), stroke='white', role='row'
            )
        return s


class LineRenderer(BaseRenderer):
    def render_rows(self, rows, legend, max_value):
        s = ''
        k = len(rows[0]['values'])
        width = self.width / len(rows)
        dots = ''
        for j in range(k):
            group = ''
            points = []
            for i, row in enumerate(rows):
                x = width * (i + 0.5)
                y = self.height * row['values'][j] / max_value
                group += self.circle(
                    x,
                    self.height - y,
                    title=self.get_title(rows, legend, i, j),
                    role='cell',
                )
                points.append((x, self.height - y))
            dots += self.element(
                'g', group, fill=self.get_color(j), stroke='white', role='row'
            )
            s += self.polyline(points, fill='none', stroke=self.get_color(j))
        s += dots
        return s


class StackedAreaRenderer(BaseRenderer):
    stacked = True

    def render_rows(self, rows, legend, max_value):
        s = ''
        k = len(rows[0]['values'])
        width = self.width / len(rows)
        prev = [(width * (i + 0.5), 1) for i in range(len(rows))]
        dots = ''
        for j in range(k):
            group = ''
            points = []
            for i, row in enumerate(rows):
                x = width * (i + 0.5)
                y = self.height * row['values'][j] / max_value
                group += self.circle(
                    x,
                    self.height - (prev[i][1] + y),
                    title=self.get_title(rows, legend, i, j),
                    role='cell',
                )
                points.append((x, prev[i][1] + y))
            dots += self.element(
                'g', group, fill=self.get_color(j), stroke='white', role='row'
            )
            s += self.polyline([
                (x, self.height - y) for x, y in points + list(reversed(prev))
            ], fill=self.get_color(j), stroke='white')
            prev = points
        s += dots
        return s


def main():
    parser = argparse.ArgumentParser(
        description='read CSV from stdin and write SVG to stdout'
    )
    parser.add_argument('-r', '--renderer', choices=[
        'column', 'stacked-column', 'line', 'stacked-area'
    ], default='line')
    args = parser.parse_args()

    cls = {
        'column': ColumnRenderer,
        'stacked-column': StackedColumnRenderer,
        'line': LineRenderer,
        'stacked-area': StackedAreaRenderer,
    }[args.renderer]

    reader = csv.reader(sys.stdin)
    data = {
        'rows': [],
        'legend': next(reader)[1:],
    }
    for row in reader:
        data['rows'].append({
            'label': row[0],
            'values': [float(i) for i in row[1:]],
        })

    renderer = cls()
    svg = renderer.render(data)
    print(svg)


if __name__ == '__main__':
    main()

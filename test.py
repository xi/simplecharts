import os
import sys
import json
import difflib

import simplecharts

DIR = 'tests'


def render_error(actual, expected, name):
    actual_lines = [line + '\n' for line in actual.split('\n')]
    expected_lines = [line + '\n' for line in expected.split('\n')]
    diff = difflib.unified_diff(
        actual_lines, expected_lines, 'actual', name)
    sys.stdout.writelines(diff)


def run_test(key, renderer):
    with open(os.path.join(DIR, key + '.json')) as fh:
        data = json.load(fh)
        actual = renderer.render(data)

    svg = '{}_{}.svg'.format(key, renderer.__class__.__name__)
    path = os.path.join(DIR, svg)

    if os.path.exists(path):
        with open(path) as fh:
            expected = fh.read()
        if renderer.render(data) != expected:
            render_error(actual, expected, svg)
    else:
        with open(path, 'w') as fh:
            fh.write(actual)
            print('generated', svg)


for fn in os.listdir(DIR):
    if fn.endswith('.json'):
        key = fn[:-5]
        run_test(key, simplecharts.ColumnRenderer())
        run_test(key, simplecharts.StackedColumnRenderer())
        run_test(key, simplecharts.LineRenderer())
        run_test(key, simplecharts.StackedAreaRenderer())

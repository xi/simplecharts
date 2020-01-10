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


def test_round_max(i, expected):
    actual = simplecharts.round_max(i)
    msg = 'round_max({}) == {} != {}'.format(i, actual, expected)
    assert actual == expected, msg


for fn in os.listdir(DIR):
    if fn.endswith('.json'):
        key = fn[:-5]
        run_test(key, simplecharts.ColumnRenderer())
        run_test(key, simplecharts.StackedColumnRenderer())
        run_test(key, simplecharts.LineRenderer())
        run_test(key, simplecharts.StackedAreaRenderer())

test_round_max(10, 20)
test_round_max(9, 10)
test_round_max(9000, 10000)
test_round_max(0.01, 0.02)
test_round_max(0.003, 0.004)

from unittest.mock import patch

from provider import provide


def test_decorator_leaves_intact():
    def function():
        return 123
    wrapped = provide(function)

    assert wrapped() == 123
    assert function == wrapped


@patch('provider.decorator.venusian')
def test_decorator_venusian_attached(venusian):
    def function():
        pass
    wrapped = provide(function)

    assert venusian.attach.call_count == 1
    assert venusian.attach.call_args[0][0] == function
    assert venusian.attach.call_args_list[0][1]['category'] == 'provider'
    assert len(venusian.attach.call_args[0]) == 2

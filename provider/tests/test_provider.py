import pytest

from provider.provider import Provider, Item
from provider.exceptions import UnknownArgumentException
from . import fixture


@pytest.fixture
def provider():
    return Provider()


def test_provider_register_callable(provider):
    def abc():
        pass
    provider.register(abc, name='fixture')

    assert provider.has('fixture')


def test_provider_register_callable_implied(provider):
    def abc():
        pass
    provider.register(abc)

    assert provider.has('abc')


@pytest.mark.parametrize('thing', [None, 123, 'abc'])
def test_provider_register_uncallable(provider, thing):
    with pytest.raises(ValueError):
        provider.register(thing)


def test_provider_register_callable_class(provider):
    class Test(object):

        def __call__(self):
            return 1
    provider.register(Test())

    assert provider.has('Test')
    assert provider.get('Test') == 1


def test_provider_get(provider):
    def abc():
        return 1
    provider.register(abc)
    result = provider.get('abc')

    assert result == 1


def test_provider_get_cached(provider):
    counter = 0

    def abc():
        nonlocal counter
        counter += 1
        return counter
    provider.register(abc)

    for i in range(2):
        result = provider.get('abc')
        assert result == 1


def test_provider_get_nonexistent(provider):
    with pytest.raises(NameError):
        provider.get('abc')


def test_scan(provider):
    # see fixture.py.
    from . import fixture
    provider.scan(fixture)

    assert provider.has('decorated_fixture')
    assert provider.get('decorated_fixture') == 1


def test_scan_order_independent(provider):
    from . import order_fixture
    provider.scan(order_fixture)

    assert provider.has('a')
    assert provider.has('b')
    assert provider.has('c')
    assert provider.get('a') == 'a'
    assert provider.get('c') == 'c'


def test_scan_missing_dependency(provider):
    from .dep_fixture import missing
    with pytest.raises(UnknownArgumentException):
        provider.scan(missing)


def test_scan_circular_dependency(provider):
    from .dep_fixture import circular
    with pytest.raises(UnknownArgumentException):
        provider.scan(circular)


def test_apply_call(provider):
    def abc():
        return 123

    def efg():
        return 456

    def test(abc):
        assert abc == 123

    def with_args(something, abc, efg, another):
        assert something == 'something'
        assert another == 'another'
        assert abc == 123
        assert efg == 456

    provider.register(abc)
    provider.register(efg)

    # Provided function with no other args
    provider.call(test)

    # Provided function with other args
    provider.call(with_args, 'something', another='another')

    # Caller can always override provides
    provider.call(with_args, 'something', 123, 456, another='another')
    provider.call(with_args, 'something', 123, 456, 'another')

    # Missing positional argument
    with pytest.raises(UnknownArgumentException):
        provider.call(with_args, another='another')

    # Missing keyword argument
    with pytest.raises(UnknownArgumentException):
        provider.call(with_args, 'something')


def test_apply_call_class(provider):
    def abc():
        return 123

    class Something(object):
        def __call__(self, abc):
            self.test(abc)

        def test(self, abc):
            assert abc == 123

    provider.register(abc)
    provider.call(Something())
    provider.call(Something().test)


def test_dependency(provider):
    def one():
        return 1

    def also_one(one):
        return one

    def two(one, also_one):
        return one + also_one

    provider.register(one)
    provider.register(also_one)
    provider.register(two)

    assert provider.get('also_one') == 1
    assert provider.get('two') == 2


def test_unsatisfied_dependency(provider):
    def test(abc):
        pass

    with pytest.raises(UnknownArgumentException):
        provider.register(test)


def test_item_from_function():
    def func():
        return 'func'

    item = Item.create_from(func)
    assert item.callable == func
    assert item.callable() == 'func'
    assert item.name == 'func'
    assert not item.klass
    assert not item.deps


def test_item_from_function_deps():
    def func(a, b, c):
        pass

    item = Item.create_from(func)
    for dep in ['a', 'b', 'c']:
        assert dep in item.deps


def test_item_from_class_instance():
    # Not callable
    with pytest.raises(ValueError):
        Item.create_from(object())

    class Callable(object):
        def __call__(self, a):
            return a

    item = Item.create_from(Callable())
    assert item.callable('Callable') == 'Callable'
    assert item.name == 'Callable'
    assert item.klass
    assert len(item.deps) == 1
    assert 'a' in item.deps


def test_item_from_bound_method():
    class Klass(object):
        def method(self, a):
            return a

    item = Item.create_from(Klass().method)
    assert item.callable('Klass') == 'Klass'
    assert item.name == 'method'
    assert item.klass
    assert len(item.deps) == 1
    assert 'a' in item.deps
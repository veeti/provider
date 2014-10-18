import inspect

import venusian

from provider.path import caller_package
from provider.exceptions import UnknownArgumentException


class Item(object):

    def __init__(self, callable, name, klass=False, deps=None):
        if not deps:
            deps = set()
        self.callable = callable
        self.name = name
        self.klass = klass
        self.deps = deps

    @staticmethod
    def create_from(thing):
        if not hasattr(thing, '__call__'):
            raise ValueError("Not a callable.")

        # Figure out what this thing is: function, class instance or bound method?
        name = getattr(thing, '__name__', '')
        if inspect.ismethod(thing):
            klass = True
        elif inspect.isfunction(thing):
            klass = False
        elif not inspect.isfunction(thing) and inspect.isclass(type(thing)):
            klass = True
            name = thing.__class__.__name__
            thing = thing.__call__

        # Get dependencies
        deps = inspect.getargspec(thing).args
        if klass:
            deps.remove('self')

        return Item(thing, name, klass, deps)


class Provider(object):

    def __init__(self):
        self._registry = dict()
        self._cache = dict()

    def register(self, thing, name=None):
        item = Item.create_from(thing)
        if not name:
            name = item.name

        # Validate dependencies
        for dep in item.deps:
            if not self.has(dep):
                raise UnknownArgumentException("Unknown dependency '{}'.".format(dep))

        self._registry[name] = item

    def has(self, name):
        return name in self._registry

    def get(self, name):
        # Check existence
        if not self.has(name):
            raise NameError("Registry does not have a provider named '{}'.".format(name))

        # Get value if not yet cached
        if not name in self._cache:
            item = self._registry[name]
            self._cache[name] = self._call(item.callable, item.klass)

        return self._cache[name]

    def scan(self, package=None):
        if not package:
            package = caller_package()

        # Scan for decorated providers
        provider = set()
        scanner = venusian.Scanner(provider=provider)
        scanner.scan(package=package, categories=['provider'])

        items = [Item.create_from(thing) for thing in provider]
        names = [item.name for item in items]
        items = {item.name: item for item in items}

        # Validate and register each item
        for name, item in items.items():
            for dep in item.deps:
                if not dep in names:
                    raise UnknownArgumentException("Unknown dependency '{}'.".format(dep))

                # Make sure this is not a circular dependency
                if dep == name or name in items[dep].deps:
                    raise UnknownArgumentException("Circular dependency '{}'".format(dep))

            self._registry[name] = item

    def call(self, function, *args, **kwargs):
        klass = False

        if inspect.ismethod(function):
            klass = True
        elif not inspect.isfunction(function) and inspect.isclass(type(function)):
            klass = True
            function = function.__call__

        return self._call(function, klass, *args, **kwargs)

    def _call(self, function, klass=False, *args, **_kwargs):
        kwargs = dict()

        # Provide arguments
        for i, arg in enumerate(inspect.getargspec(function).args):
            if not i >= len(args) or (klass and arg == 'self'):
                # The user's positional arguments come first, and bound methods obviously have self.
                continue

            if self.has(arg):
                kwargs[arg] = self.get(arg)
            elif arg not in _kwargs:
                # We don't have a provider with this name and the user didn't give one either.
                raise UnknownArgumentException("Unsatisfied argument '{}'.".format(arg))

        # Overlay the user's keyword arguments on top of ours
        kwargs.update(_kwargs)

        return function(*args, **kwargs)

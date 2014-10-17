import inspect

import venusian

from provider.path import caller_package
from provider.exceptions import UnknownArgumentException


class Item(object):

    def __init__(self, callable, klass=False):
        self.callable = callable
        self.klass = klass


class Provider(object):

    def __init__(self):
        self._registry = dict()
        self._cache = dict()

    def register(self, thing, name=None):
        # Can only register a callable
        if not hasattr(thing, '__call__'):
            raise ValueError("Not a callable.")

        # Is this a class instance?
        klass = not inspect.isfunction(thing) and inspect.isclass(type(thing))

        # Use object name if implied
        if not name:
            if not klass:
                name = thing.__name__
            else:
                name = thing.__class__.__name__

        if klass:
            thing = thing.__call__

        # Make sure we have its dependencies
        for dep in inspect.getargspec(thing).args:
            if klass and dep == 'self':
                continue
            if not self.has(dep):
                raise UnknownArgumentException("Provider depends on unknown provider '{}'.".format(dep))

        self._registry[name] = Item(thing, klass)

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

        scanner = venusian.Scanner(provider=self)
        scanner.scan(package=package, categories=['provider'])

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

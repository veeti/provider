import inspect

import venusian

from provider.path import caller_package
from provider.exceptions import UnknownArgumentException


class Provider(object):

    def __init__(self):
        self._registry = dict()
        self._cache = dict()

    def register(self, thing, name=None):
        # Can only register a callable
        if not hasattr(thing, '__call__'):
            raise ValueError("Not a callable.")

        # Use object name if implied
        if not name:
            name = thing.__name__

        # Make sure we have its dependencies
        for dep in inspect.getargspec(thing).args:
            if not self.has(dep):
                raise UnknownArgumentException("Provider depends on unknown provider '{}'.".format(dep))

        self._registry[name] = thing

    def has(self, name):
        return name in self._registry

    def get(self, name):
        # Check existence
        if not self.has(name):
            raise NameError("Registry does not have a provider named '{}'.".format(name))

        # Get value if not yet cached
        if not name in self._cache:
            self._cache[name] = self.call(self._registry[name])

        return self._cache[name]

    def scan(self, package=None):
        if not package:
            package = caller_package()

        scanner = venusian.Scanner(provider=self)
        scanner.scan(package=package, categories=['provider'])

    def call(self, function, *args, **_kwargs):
        kwargs = dict()

        # Provide arguments
        for i, arg in enumerate(inspect.getargspec(function).args):
            if not i >= len(args):
                # The user's positional arguments come first
                continue

            if self.has(arg):
                kwargs[arg] = self.get(arg)
            elif arg not in _kwargs:
                # We don't have a provider with this name and the user didn't give one either.
                raise UnknownArgumentException("Unsatisfied argument '{}'.".format(arg))

        # Overlay the user's keyword arguments on top of ours
        kwargs.update(_kwargs)

        return function(*args, **kwargs)

import venusian


def provide(fn):
    def callback(scanner, name, ob):
        if hasattr(scanner, 'provider'):
            scanner.provider.register(fn)
        return fn
    venusian.attach(fn, callback, category='provider')
    return fn


# provider

**provider** is a "registry system" inspired by [py.test fixtures](http://pytest.org/latest/fixture.html#fixture). It allows you to inject dependencies to functions based on argument names. Work in progress.

## Example

```python
from provider import Provider

def hello():
    return "Hello, world!"

def printer(message):
    print(message)

injector = Provider()
injector.register(hello, name='message')
injector.call(printer) # => "Hello, world!"
```

(Yes, contrived.)

You can also decorate provider functions with `@provide` and call `scan()` on the registry object to discover them.

## What's the point?

Practical application pending. One idea is a Pyramid view mapper allowing arbitrary signatures:

```python
def my_view(request, database, some_other_service):
    database.get_by_id(request.params['id'])
    some_other_service.do_stuff()
    ...
```

## License

MIT. See `LICENSE`.
from provider import provide

@provide
def b():
    return 'b'


@provide
def c(a):
    return chr(ord(a) + 2)
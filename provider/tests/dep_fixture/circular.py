from provider import provide

@provide
def a(b):
    pass

@provide
def b(a):
    pass
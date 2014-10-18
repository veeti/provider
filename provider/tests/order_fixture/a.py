from provider import provide

@provide
def a(b):
    return chr(ord(b) - 1)
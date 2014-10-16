from provider import provide


@provide
def decorated_fixture():
    return 1
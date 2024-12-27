

static_setattr = object.__setattr__
static_getattr = object.__getattribute__

__all__ = ["static_getattr", "static_setattr", "static_hasattr", ]

def static_hasattr(obj: object, name: str) -> bool:
    try:
        static_getattr(obj, name)
        return True
    except AttributeError:
        return False


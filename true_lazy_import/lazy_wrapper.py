

import sys
from typing import Any

def _noop(*args, **kwargs) -> Any: pass


if sys.version_info >= (3, 14):
    from annotationlib import ForwardRef
else:
    from typing import ForwardRef
    

# cursed hack to allow subclassing ForwardRef
_old_init_subclass = ForwardRef.__init_subclass__
ForwardRef.__init_subclass__ = _noop


class LazyImportedType(ForwardRef): # type: ignore
    def __init__(self, arg, *, module=None, owner=None, is_argument=True, is_class=False):
        if sys.version_info >= (3, 14):
            super().__init__(arg, module=module, owner=owner, is_argument=is_argument, is_class=is_class)
        else:
            super().__init__(arg, module=module, is_argument=is_argument, is_class=is_class)

ForwardRef.__init_subclass__ = _old_init_subclass


    
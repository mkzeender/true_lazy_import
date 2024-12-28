

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


class LazyImportedType(ForwardRef):
    ...

ForwardRef.__init_subclass__ = _old_init_subclass


    
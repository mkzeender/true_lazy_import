"""
Mostly copied from _bootstrap.py and importlib
"""

from importlib.machinery import ModuleSpec
from importlib.util import find_spec, module_from_spec
from types import ModuleType
from typing import Sequence
import warnings
from true_lazy_import._module_tools import static_getattr, static_hasattr, static_setattr
from true_lazy_import.exceptions import LazyImportRuntimeError
import sys

from true_lazy_import.lazy_loader import LazyLoader
from true_lazy_import.lazy_module import LoaderState
from true_lazy_import.lazy_wrapper import LazyImportedType

builtin_module_names = set(sys.builtin_module_names)


def handle_fromlist(module: ModuleType, fromlist: Sequence[str]):
    """For "from ... import ..." statements

    The import_ parameter is a callable which takes the name of module to
    import. It is required to decouple the function from assuming importlib's
    import implementation is desired.

    """
    # The hell that is fromlist ...
    # If a package was imported, try to import sub-packages from fromlist.
    is_package = static_hasattr(module, '__path__')
    module_name: str = static_getattr(module, '__name__')
    loader_state: LoaderState|None = getattr(static_getattr(module, '__spec__'), 'loader_state', None)
    for imported_name in fromlist:
        if imported_name == '*':
            raise LazyImportRuntimeError('Cannot use "import *" with lazy importing.')

        if static_hasattr(module, imported_name):
            continue
        
        if is_package:
            sub_pkg_name = f'{module_name}.{imported_name}'

            try:
                lazy_gcd_import(sub_pkg_name)
            except ModuleNotFoundError as exc:
                # Backwards-compatibility dictates we ignore failed
                # imports triggered by fromlist for modules that don't
                # exist.
                if not (exc.name == sub_pkg_name):
                    raise
            
        if not static_hasattr(module, imported_name):
            fwdref = LazyImportedType(
                imported_name,
                module=module_name,
                owner=module,
                is_class=False
            )
            static_setattr(module, imported_name, fwdref)
            if loader_state:
                loader_state.dict[imported_name] = fwdref
            
    return module


def lazy_gcd_import(name: str):
    """Import and return the module based on its name, the package the call is
    being made from, and the level adjustment.

    This function represents the greatest common denominator of functionality
    between import_module and __import__. This includes setting __package__ if
    the loader did not.

    """
    if name in sys.modules:
        return sys.modules[name]
    
    parent = name.rpartition('.')[0]
    if parent:
        parent_module = lazy_gcd_import(parent)
        
        child_name = name.rpartition('.')[2]

        module = _create_lazy_module(name)
        
        # Set the module as an attribute on its parent.
        try:
            static_setattr(parent_module, child_name, module)
        except AttributeError:
            msg = f"Cannot set an attribute on {parent!r} for child module {child_name!r}"
            warnings.warn(msg, ImportWarning)

        loader_state: LoaderState|None = getattr(parent_module.__spec__, 'loader_state')
        if loader_state:
            loader_state.dict[child_name] = module
    else:
        module = _create_lazy_module(name)
    return module



def _create_lazy_module(name: str) -> ModuleType:

        spec: ModuleSpec|None = find_spec(name) # recursively imports the parent package.
        if spec is None or spec.loader is None:
            raise ModuleNotFoundError(name=name)

        loader = LazyLoader(spec.loader)

        spec.loader = loader

        module = module_from_spec(spec)

        sys.modules[name] = module

        loader.exec_module(module)

        return module
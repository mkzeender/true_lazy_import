from dataclasses import dataclass, field
import sys
from threading import RLock
import types
from types import ModuleType
from typing import TypeIs
from true_lazy_import._module_tools import static_getattr, static_hasattr, static_setattr
from true_lazy_import.exceptions import LazyImportRuntimeError, NotLazyEnoughError
from importlib.machinery import ModuleSpec


# EXEMPT_ATTRS = {'__name__', '__spec__', '__package__', '__loader__', '__path__', '__file__', '__cached__'}


@dataclass
class LoaderState:
    dict: dict[str, object]
    cls: type[types.ModuleType]
    lock: RLock = field(default_factory=RLock)
    is_loading: bool = False
    allow_loading: bool = False


class LazyModule(types.ModuleType):

    """
    Based on importlib.util._LazyModule
    """


    def __getattribute__(self, attr:str):
        """If lazy loading is still enabled, create forward references, otherwise, load the module and get the result."""
        spec:ModuleSpec = static_getattr(self, '__spec__')
        loader_state: LoaderState = spec.loader_state
        assert spec.loader is not None


        if not loader_state.allow_loading:
            if static_hasattr(self, attr):
                return static_getattr(self, attr)
            raise NotLazyEnoughError(f'Attribute "{attr}" of module <{spec.name}> was accessed before it was loaded.')
        else:
            with loader_state.lock:
                # Only the first thread to get the lock should trigger the load
                # and reset the module's class. The rest can now getattr().
                if static_getattr(self, '__class__') is LazyModule:
                    loaded_module_class = loader_state.cls

                    # Reentrant calls from the same thread must be allowed to proceed without
                    # triggering the load again.
                    # exec_module() and self-referential imports are the primary ways this can
                    # happen, but in any case we must return something to avoid deadlock.
                    if loader_state.is_loading:
                        return static_getattr(self, attr)
                    loader_state.is_loading = True

                    module_dict: dict[str, object] = static_getattr(self, '__dict__')

                    # All module metadata must be gathered from __spec__ in order to avoid
                    # using mutated values.
                    # Get the original name to make sure no object substitution occurred
                    # in sys.modules or in the parent package.
                    original_name: str = spec.name
                    parent_name, _, root_name = original_name.rpartition('.')
                    if parent_name:
                        # recursively call __getattribute__ on parent package, loading it.
                        if self is not getattr(sys.modules.get(parent_name, None), root_name, None):
                            raise LazyImportRuntimeError(f"module object for {original_name!r} "
                                            f"substituted in parent package {parent_name!r} during a lazy "
                                            "load")
                        
                    # Figure out exactly what attributes were mutated between the creation
                    # of the module and now.
                    attrs_then: dict[str, object] = loader_state.dict
                    attrs_now = module_dict
                    attrs_updated: dict[str, object] = {}
                    for key, value in attrs_now.items():
                        # Code that set an attribute may have kept a reference to the
                        # assigned object, making identity more important than equality.
                        if key not in attrs_then:
                            attrs_updated[key] = value
                        elif attrs_now[key] is not attrs_then[key]:
                            attrs_updated[key] = value
                    spec.loader.exec_module(self)
                    # If exec_module() was used directly there is no guarantee the module
                    # object was put into sys.modules.
                    if original_name in sys.modules:
                        if self is not sys.modules[original_name]:
                            raise LazyImportRuntimeError(f"module object for {original_name!r} "
                                            "substituted in sys.modules during a lazy "
                                            "load")
                    # Update after loading since that's what would happen in an eager
                    # loading situation.
                    module_dict.update(attrs_updated)
                    # Finally, stop triggering this method, if the module did not
                    # already update its own __class__.
                    if isinstance(self, LazyModule):
                        static_setattr(self, '__class__', loaded_module_class)

            return getattr(self, attr)
        
            

    def __delattr__(self, attr):
        """Trigger the load and then perform the deletion."""
        # To trigger the load and raise an exception if the attribute
        # doesn't exist.
        self.__getattribute__(attr)
        delattr(self, attr)


def is_lazy_module(mod: ModuleType) -> TypeIs[LazyModule]:
    return static_getattr(mod, '__class__') is LazyModule
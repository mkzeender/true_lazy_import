import builtins
from collections.abc import Sequence
from importlib.machinery import ModuleSpec
import importlib.util
from sys import modules, builtin_module_names
from threading import RLock
from types import ModuleType
from typing import Any, Literal, Protocol, Self

from true_lazy_import._module_tools import static_getattr
from true_lazy_import.import_tools import handle_fromlist, lazy_gcd_import
from true_lazy_import.lazy_module import LoaderState


_exempt_modules = set(builtin_module_names)
_exempt_modules.add('threading')


class Importer(Protocol):
    def __call__(
        self,
        name:str,
        globals:dict[str, Any]|None=None,
        locals: dict[str, Any]|None=None,
        fromlist: Sequence[str]=(),
        level:int=0
    ) -> ModuleType: ...


class LazyContextMgr:
    def __init__(self):
        self.lock = RLock()
        self.recursive_level = 0
        self._old_import: Importer
        self._current_module: ModuleType
        self._is_enabled = False
        self._active_states: list[LoaderState]

    def __repr__(self):
        return 'lazy_import.lazy'

    def __enter__(self) -> Self:
        self.enable()
        return self

    def __exit__(self, *exc_info) -> Literal[False]:
        self.disable()
        return False

    def enable(self):
        self.lock.acquire()
        if self._is_enabled:
            self.lock.release()
            raise RuntimeError('Lazy Import is already enabled. Make sure to only use "import" statements within a "with lazy:" block')
        self._active_states = []
        self._enable()

    def disable(self):
        if not self._is_enabled:
            raise RuntimeError('Lazy Import is already disabled.')

        for state in self._active_states:
            state.allow_loading = True
        del self._active_states
        self._disable()
        self.lock.release()

    def _enable(self):
        
        self._old_import = builtins.__import__
        self._is_enabled = True
        builtins.__import__ = self.lazy_importer

    def _disable(self):
        builtins.__import__ = self._old_import
        del self._old_import
        self._is_enabled = False

    @property
    def is_enabled(self):
        return self._is_enabled

    def _import_exempt_module(
        self,
        name:str,
        globals:dict[str, Any]|None=None,
        locals: dict[str, Any]|None=None,
        fromlist: Sequence[str]=(),
        level:int=0
    ) -> ModuleType:
        self.disable()
        try:
            return builtins.__import__(name, globals, locals, fromlist, level)
        finally:
            self.enable()
            

    def lazy_importer(
        self,
        name:str,
        globals:dict[str, Any]|None=None,
        locals: dict[str, Any]|None=None,
        fromlist: Sequence[str]=(),
        level:int=0
    ) -> ModuleType:

        package_name: str|None = globals.get('__package__', None) if globals else None
        full_name = importlib.util.resolve_name('.'*level + name, package_name)

        if full_name in _exempt_modules:
            return self._import_exempt_module(name, globals, locals, fromlist, level)

        module = lazy_gcd_import(full_name)
        
        if fromlist: # i.e. "from NAME import FROMLIST"
            return handle_fromlist(module, fromlist)

        else: # i.e. "import NAME"
            if level == 0:
                return modules[name.partition('.')[0]]
            elif not name:
                return module
            else:
                # Figure out where to slice the module's name up to the first dot
                # in 'name'.
                cut_off = len(name) - len(name.partition('.')[0])
                # Slice end needs to be positive to alleviate need to special-case
                # when ``'.' not in name``.
                _mod_name: str = static_getattr(module, '__name__')
                return modules[_mod_name[:len(_mod_name)-cut_off]]
            
        

    
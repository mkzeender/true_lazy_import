
# from types import ModuleType
# from typing import Any
# from annotationlib import Format, get_annotations
# from functools import cached_property
# from sys import modules
# from importlib import import_module

# from lazy_import.lazy_module import LazyModule

# type NT = dict[str, object] | None

# set_attrib = object.__setattr__
# get_attrib = object.__getattribute__


# class LazyWrapper:
#     def __init__(self, name: str, module:str) -> None:
#         self.__name__ = name
#         self.__module__ = module
#         self.__qualname__ = name

#     @cached_property
#     def __wrapped__(self) -> object:
#         return self._evaluate_()

#     @property
#     def __origin__(self) -> object:
#         return self.__wrapped__

#     def _evaluate_(self, fmt: Format=Format.VALUE):
#         mod = self.__module__
#         if fmt == Format.STRING:
#             return self.__name__
        
#         if fmt == Format.VALUE:
#             if mod not in modules:
#                 raise AttributeError(f"'{self.__name__}' does not (yet) exist in module {self.__module__}", name=self.__name__, obj=self.__module__)
#             return getattr(modules[mod], self.__name__)

#         if fmt == Format.FORWARDREF:
#             try:
#                 return self._evaluate_(Format.VALUE)
#             except AttributeError:
#                 pass

#     def __annotate__(self, fmt: Format) -> dict[str, object]:
#         return get_annotations(self._evaluate_(fmt))

#     @cached_property
#     def __annotations__(self) -> dict[str, Any]: # type: ignore
#         return self.__annotate__(Format.VALUE)

    


from annotationlib import ForwardRef


# cursed hack to allow subclassing ForwardRef
_old_init_subclass = ForwardRef.__init_subclass__
del ForwardRef.__init_subclass__

class LazyImportedType(ForwardRef):
    ...


ForwardRef.__init_subclass__ = _old_init_subclass
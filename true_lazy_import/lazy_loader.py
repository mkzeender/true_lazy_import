from importlib.abc import Loader
import true_lazy_import


from true_lazy_import.lazy_module import LazyModule, LoaderState





class LazyLoader(Loader):

    """A loader that creates a module which defers loading until attribute access."""

    def __init__(self, loader):
        self.loader = loader

    def create_module(self, spec):
        return self.loader.create_module(spec)

    def exec_module(self, module):
        """Make the module load lazily."""
        # Threading is only needed for lazy loading, and importlib.util can
        # be pulled in at interpreter startup, so defer until needed.
        assert module.__spec__ is not None
        module.__spec__.loader = self.loader
        module.__loader__ = self.loader
        # Don't need to worry about deep-copying as trying to set an attribute
        # on an object would have triggered the load,
        # e.g. ``module.__spec__.loader = None`` would trigger a load from
        # trying to access module.__spec__.
        loader_state = LoaderState(module.__dict__.copy(), module.__class__)
        true_lazy_import.lazy._active_states.append(loader_state)

        module.__spec__.loader_state = loader_state
        module.__class__ = LazyModule


def test_imports():
    from true_lazy_import import lazy
    with lazy:
        import spam
        import spam.ham
        from spam import ham
        from spam import foo

    from true_lazy_import.lazy_module import LazyModule

    assert isinstance(spam, LazyModule)
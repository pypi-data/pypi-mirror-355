import pytest


def test_namespace_alias():
    with pytest.raises(ImportError):
        from graphex import nx


def test_namespace_nesting():
    with pytest.raises(ImportError):
        from graphex import networkx

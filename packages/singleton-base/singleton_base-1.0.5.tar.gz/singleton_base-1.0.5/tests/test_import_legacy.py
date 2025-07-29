class TestImportsLegacy:
    """Test class for checking imports of singleton base classes."""

    def test_imports(self):
        """Test that the correct singleton base class is imported"""
        import sys

        from singleton_base import SingletonBase as ImportedBase
        from singleton_base.singleton_base_legacy import SingletonBase as LegacyBase

        if sys.version_info < (3, 11):
            assert isinstance(ImportedBase, type(LegacyBase))
        else:
            assert not isinstance(ImportedBase, type(LegacyBase)), "SingletonBase should not be of type LegacyBase"

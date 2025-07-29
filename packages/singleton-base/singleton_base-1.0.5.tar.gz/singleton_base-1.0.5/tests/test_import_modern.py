class TestImportsModern:
    """Test class for checking imports of singleton base classes."""

    def test_imports(self):
        """Test that the correct singleton base class is imported"""
        import sys

        from singleton_base import SingletonBase as ImportedBase

        if sys.version_info < (3, 11):
            from singleton_base.singleton_base_legacy import SingletonBase as LegacyBase

            assert isinstance(ImportedBase, type(LegacyBase)), "SingletonBase should be of type LegacyBase"
        else:
            from singleton_base.singleton_base_new import SingletonBase as NewBase

            assert isinstance(ImportedBase, type(NewBase)), "SingletonBase should be of type NewBase"

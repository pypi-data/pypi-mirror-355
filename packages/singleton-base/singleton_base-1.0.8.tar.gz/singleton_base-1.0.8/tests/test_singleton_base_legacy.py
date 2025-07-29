# tests to ensure the singleton behavior of SingletonBase ## KEEP THIS TEST ##
import pytest

from src.singleton_base import SingletonBase


class TestSingletonBase:
    def test_singleton_instance(self):
        class ExampleSingleton(SingletonBase):
            def __init__(self, value: int):
                self.value = value

        instance1 = ExampleSingleton.get_instance(init=True, value=42)
        instance2 = ExampleSingleton.get_instance()

        assert instance1 is instance2
        assert instance1.value == 42

    def test_singleton_reset(self):
        class ExampleSingleton(SingletonBase):
            def __init__(self, value: int):
                self.value = value

        instance1 = ExampleSingleton.get_instance(init=True, value=42)
        ExampleSingleton.reset_instance()
        instance2 = ExampleSingleton.get_instance(init=True, value=100)

        assert instance1 is not instance2
        assert instance2.value == 100

    def test_singleton_has_instance(self):
        class ExampleSingleton(SingletonBase):
            def __init__(self, value: int):
                self.value = value

        assert not ExampleSingleton.has_instance()
        ExampleSingleton.get_instance(init=True, value=42)
        assert ExampleSingleton.has_instance()

    def test_runtime_error_uninitialized_instance(self):
        """Test that RuntimeError is raised when getting uninitialized instance."""

        class ExampleSingleton(SingletonBase):
            def __init__(self, value: int):
                self.value = value

        ExampleSingleton.reset_instance()

        with pytest.raises(RuntimeError, match="Instance of ExampleSingleton is not initialized yet"):
            ExampleSingleton.get_instance()

    def test_direct_instantiation_singleton_behavior(self):
        """Test that direct instantiation via constructor follows singleton pattern."""

        class ExampleSingleton(SingletonBase):
            def __init__(self, value: int):
                self.value = value

        ExampleSingleton.reset_instance()

        instance1 = ExampleSingleton(42)
        instance2 = ExampleSingleton(100)  # This should return the same instance

        assert instance1 is instance2
        assert instance1.value == 42
        assert instance2.value == 42

    def test_multiple_singleton_classes_isolation(self):
        """Test that different singleton classes maintain separate instances."""

        class SingletonA(SingletonBase):
            def __init__(self, value: str):
                self.value = value

        class SingletonB(SingletonBase):
            def __init__(self, value: int):
                self.value = value

        SingletonA.reset_instance()
        SingletonB.reset_instance()

        instance_a = SingletonA.get_instance(init=True, value="A")
        instance_b = SingletonB.get_instance(init=True, value=1)

        assert instance_a is not instance_b
        assert instance_a.value == "A"
        assert instance_b.value == 1

        instance_a2 = SingletonA.get_instance()
        instance_b2 = SingletonB.get_instance()

        assert instance_a is instance_a2
        assert instance_b is instance_b2

    def test_reset_instance_clears_has_instance(self):
        """Test that has_instance() returns False after reset_instance()."""

        class ExampleSingleton(SingletonBase):
            def __init__(self, value: int):
                self.value = value

        # Create instance
        ExampleSingleton.get_instance(init=True, value=42)
        assert ExampleSingleton.has_instance()

        # Reset and verify
        ExampleSingleton.reset_instance()
        assert not ExampleSingleton.has_instance()

    def test_singleton_no_constructor_args(self):
        """Test singleton behavior with no constructor arguments."""

        class ExampleSingleton(SingletonBase):
            def __init__(self):
                self.initialized = True

        ExampleSingleton.reset_instance()

        instance1 = ExampleSingleton.get_instance(init=True)
        instance2 = ExampleSingleton.get_instance()

        assert instance1 is instance2
        assert instance1.initialized

    def test_singleton_multiple_constructor_args(self):
        """Test singleton behavior with multiple constructor arguments."""

        class ExampleSingleton(SingletonBase):
            def __init__(self, value1: int, value2: str, value3: bool = False):
                self.value1 = value1
                self.value2 = value2
                self.value3 = value3

        ExampleSingleton.reset_instance()

        instance1 = ExampleSingleton.get_instance(init=True, value1=1, value2="test", value3=True)
        instance2 = ExampleSingleton.get_instance()

        assert instance1 is instance2
        assert instance1.value1 == 1
        assert instance1.value2 == "test"
        assert instance1.value3 is True

    def test_singleton_mixed_instantiation_methods(self):
        """Test mixing direct instantiation and get_instance() methods."""

        class ExampleSingleton(SingletonBase):
            def __init__(self, value: int):
                self.value = value

        ExampleSingleton.reset_instance()
        instance1 = ExampleSingleton(42)

        instance2 = ExampleSingleton.get_instance()

        instance3 = ExampleSingleton(100)

        assert instance1 is instance2 is instance3
        assert instance1.value == 42

    def test_singleton_inheritance_chain(self):
        """Test singleton behavior with inheritance."""

        class BaseSingleton(SingletonBase):
            def __init__(self, base_value: int):
                self.base_value = base_value

        class DerivedSingleton(BaseSingleton):
            def __init__(self, base_value: int, derived_value: str):
                super().__init__(base_value)
                self.derived_value = derived_value

        DerivedSingleton.reset_instance()

        instance1 = DerivedSingleton.get_instance(init=True, base_value=42, derived_value="test")
        instance2 = DerivedSingleton.get_instance()

        assert instance1 is instance2
        assert instance1.base_value == 42
        assert instance1.derived_value == "test"

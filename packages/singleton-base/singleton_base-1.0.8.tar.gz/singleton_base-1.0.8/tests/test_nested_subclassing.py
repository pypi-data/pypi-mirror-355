"""Tests the singleton base class to see if it works with nested subclassing."""

from src.singleton_base import SingletonBase


class ExampleSingleton(SingletonBase):
    """Example singleton class."""

    def __init__(self):
        super().__init__()
        self.value = 42


class NestedSingleton(ExampleSingleton):
    """Nested singleton class."""

    def __init__(self):
        super().__init__()
        self.nested_value = "Hello, World!"


def test_nested_singleton():
    """Test the nested singleton class."""
    example_singleton: ExampleSingleton = ExampleSingleton.get_instance(init=True)
    nested_singleton: NestedSingleton = NestedSingleton.get_instance(init=True)

    example_id: int = id(example_singleton)
    nested_id: int = id(nested_singleton)

    print(f"ExampleSingleton ID: {example_id}, NestedSingleton ID: {nested_id}")

    assert example_id != nested_id, "Expected different instances for ExampleSingleton and NestedSingleton"

    example2: ExampleSingleton = ExampleSingleton.get_instance(init=True)
    nested2: NestedSingleton = NestedSingleton.get_instance(init=True)
    example2_id: int = id(example2)
    nested2_id: int = id(nested2)

    print(f"ExampleSingleton ID (2): {example2_id}, NestedSingleton ID (2): {nested2_id}")

    assert example_id == example2_id, "Expected same instance for ExampleSingleton"
    assert nested_id == nested2_id, "Expected same instance for NestedSingleton"

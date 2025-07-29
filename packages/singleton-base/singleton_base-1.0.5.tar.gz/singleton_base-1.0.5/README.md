# singleton-base

A type-friendly, thread-safe singleton base class for Python 3.9+. Very simple to use and test-friendly.

## Installation

### Using pip

```bash
pip install singleton-base
```

### Using Uv

```bash
uv add singleton-base
```

### Using Poetry

```bash
poetry add singleton-base
```

## Features

- Thread-safe: Multiple threads can safely create instances
- Type-friendly: Full type hint support with modern typing on Python 3.11+
- Version adaptive: Automatically uses legacy implementation on Python < 3.11
- Test-friendly: Easy instance management for testing scenarios

## Usage

### Usage Example

Subclass using SingletonBase to make your class a singleton. All returned instances will now be the same object.

```python
from singleton_base import SingletonBase


class MySingleton(SingletonBase):
    """A singleton class example that holds an integer value."""

    def __init__(self, value: int):
        self.value = value


class AnotherSingleton(SingletonBase):
    """Another singleton class example that holds a string value."""

    def __init__(self, value: str):
        self.value = value


# Check if instance exists (initially False)
print(f"Instance Exists: {MySingleton.has_instance()}")  # False

# Two ways to create the singleton (both do the same thing):
instance = MySingleton(42)

# Safe pattern - always use init=True when instance might not exist
instance: MySingleton = MySingleton.get_instance(init=True, value=42)
print(f"Instance Exists: {MySingleton.has_instance()}, Value: {instance.value}")  # True

instance2: MySingleton = MySingleton.get_instance()

print(f"Same instance: {instance is instance2}")  # True

# Other singleton classes can be created independently
another_instance: AnotherSingleton = AnotherSingleton.get_instance(init=True, value="Hello")
print(f"Same instance: {instance2 is another_instance}")  # False

# This will raise RuntimeError: calling get_instance() without init=True when no instance exists:
try:
    MySingleton.reset_instance()
    instance = MySingleton.get_instance()  # RuntimeError
except RuntimeError as e:
    print(e)  # Instance of MySingleton is not initialized yet

print(f"Instance Exists: {MySingleton.has_instance()}")  # False

instance = MySingleton.get_instance(init=True, value=69)

# an alternative way to do this is to check using has_instance
if MySingleton.has_instance():
    instance = MySingleton.get_instance()
    print(f"Instance Already Exists: {MySingleton.has_instance()}, Value: {instance.value}")  # 69
else:
    instance = MySingleton.get_instance(init=True, value=9001)
    print(f"Instance Created: {MySingleton.has_instance()}, Value: {instance.value}")  # Won't be printed

```

### Available Methods

| Method                             | Description                                                      |
| ---------------------------------- | ---------------------------------------------------------------- |
| get_instance(init=False, **kwargs) | Returns singleton instance. If init=True, creates it with kwargs |
| has_instance()                     | Returns True if singleton instance exists                        |
| reset_instance()                   | Destroys current instance, allows creating a new one             |

## Python Version Compatibility

Python 3.11+ uses modern implementation with more modern type hints.
Python 3.9-3.10 automatically falls back to legacy implementation.
Full test coverage across all supported versions.

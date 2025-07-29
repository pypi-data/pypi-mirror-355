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
    print(f"Instance Created: {MySingleton.has_instance()}")  # Won't be printed

import random
from threading import Thread
from time import sleep

import pytest

from singleton_base import SingletonBase


class ExampleSingleton(SingletonBase):
    def __init__(self, value):
        sleep(random.uniform(0.01, 0.5))
        self.value = value


@pytest.mark.parametrize("thread_count", [5, 10, 20, 50])
def test_thread_safety(thread_count):
    """Test that multiple threads can create instances of the singleton class"""
    ExampleSingleton.reset_instance()

    instances: list[ExampleSingleton] = []

    def create_instance(value):
        instance = ExampleSingleton(value)
        instances.append(instance)

    threads = []
    print(f"\nStarting {thread_count} threads to create singleton instances...")
    for i in range(thread_count):
        thread: Thread = Thread(target=create_instance, args=(i,))
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    unique_instances = set(id(instance) for instance in instances)

    assert len(unique_instances) == 1, f"Expected one unique instance, got {len(unique_instances)}"
    assert len(instances) == thread_count, f"Expected {thread_count} instances, got {len(instances)}"

from threading import RLock
from typing import Any, ClassVar, Self

INSTANCE_NAME = "_instance_{instance_name}"


class SingletonMeta(type):
    """Metaclass that enforces the singleton pattern."""

    _lock: ClassVar[RLock] = RLock()

    def __call__(cls, *args, **kwargs) -> Any:
        class_attr_name: str = INSTANCE_NAME.format(instance_name=cls.__name__)
        if not getattr(cls, class_attr_name, False):
            with cls._lock:
                if not getattr(cls, class_attr_name, False):
                    setattr(cls, class_attr_name, super().__call__(*args, **kwargs))
        return getattr(cls, class_attr_name)


class SingletonBase(metaclass=SingletonMeta):
    """A base class for singleton classes"""

    # region Private Class Methods

    @classmethod
    def __instance(cls) -> Self:
        """Method used when we know the instance is present"""
        return getattr(cls, cls._instance_attr())

    @classmethod
    def __set_instance(cls, value: Self | None) -> None:
        """Set the singleton instance to a new value"""
        setattr(cls, cls._instance_attr(), value)

    @classmethod
    def __get_instance(cls) -> Self | None:
        """Get the singleton instance, or None if it does not exist"""
        return getattr(cls, cls._instance_attr(), None)

    @classmethod
    def _instance_attr(cls) -> str:
        """Get the name of the class attribute that holds the singleton instance."""
        return INSTANCE_NAME.format(instance_name=cls.__name__)

    # endregion

    # region Public Class Methods

    @classmethod
    def get_instance(cls, init: bool = False, **kwargs) -> Self:
        """
        Return the singleton instance. If the instance does not yet exist, it is created using the provided
        arguments. Uses a lock to ensure thread safety.

        Args:
            init: Whether to initialize the instance if it does not yet exist.
            **kwargs: Arguments passed to ``cls`` when creating the instance.

        Returns:
            Self: The singleton instance of the class.

        Raises:
            RuntimeError: If ``init`` is ``False`` and the instance has not been initialized.
        """

        if not cls.has_instance() and not init:
            raise RuntimeError(f"Instance of {cls.__name__} is not initialized yet")
        elif not cls.has_instance() and init:
            with cls._lock:
                if not cls.has_instance():
                    cls.__set_instance(cls(**kwargs))
        return cls.__instance()

    @classmethod
    def has_instance(cls) -> bool:
        """
        Return ``True`` if the singleton instance has been initialized.

        Returns:
            bool: ``True`` if the instance exists, ``False`` otherwise.
        """
        return cls.__get_instance() is not None

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance to allow re-initialization.

        Uses a lock to ensure thread safety.
        """
        with cls._lock:
            cls.__set_instance(None)

    # endregion

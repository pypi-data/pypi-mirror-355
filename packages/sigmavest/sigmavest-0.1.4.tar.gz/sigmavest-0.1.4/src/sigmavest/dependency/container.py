from typing import Callable, TypeVar

T = TypeVar("T")


class Container:
    def __init__(self):
        self._factories = {}
        self._instances = {}

    def register_factory(self, interface, factory: Callable):
        self._factories[interface] = factory

    def resolve(self, interface: type[T]) -> T:
        if interface not in self._instances:
            self._create_instance(interface)
        return self._instances[interface]

    def _create_instance(self, interface):
        if interface not in self._factories:
            msg = f"Cannot resolve dependency '{interface}' as it is not registered."
            raise KeyError(msg)
        factory = self._factories[interface]
        self._instances[interface] = factory(self)

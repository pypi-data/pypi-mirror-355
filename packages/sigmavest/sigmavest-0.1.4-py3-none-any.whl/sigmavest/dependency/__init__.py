import importlib
from typing import TypeVar
from .container import Container

from ..settings import Settings, get_settings

def create_container() -> Container:
    container = Container()

    container.register_factory(Settings, lambda c: get_settings())

    settings:Settings = container.resolve(Settings)
    register_components(container, settings.DEPENDENCY_AUTO_REGISTER)
    return container


def register_components(c: Container, components: list):
    for component in components:
        component: str
        try:
            module_ref, _, func_name = component.partition(":")
            module = importlib.import_module(module_ref)
            func_name = func_name or "register"

            func = getattr(module, func_name)
            func(c)
        except Exception as e:
            msg = f"Error registering {component}: {str(e)}"
            raise ImportError(msg)

T = TypeVar('T')

def resolve(interface: type[T]) -> T:
    container = create_container()
    return container.resolve(interface)

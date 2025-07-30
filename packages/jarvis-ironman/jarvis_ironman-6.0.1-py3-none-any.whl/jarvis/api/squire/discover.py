import os
import pathlib
import warnings
from collections.abc import Generator
from importlib import import_module
from typing import List

from fastapi import APIRouter

from jarvis.api.logger import logger


class Entrypoint:
    """Wrapper for Entrypoint object.

    >>> Entrypoint

    Args:
        module: Router path in the form of a module.
        stem: Bare name of the module.
    """

    def __init__(self, module: str, stem: str):
        """Wraps entry point into an object."""
        self.module = module
        self.stem = stem


def get_entrypoints(routers: str) -> Generator[Entrypoint]:
    """Get all the routers as a module that can be imported.

    Args:
        routers: Directory name where the potential router modules are present.

    See Also:
        The attribute within the module should be named as ``router`` for the auto discovery to recognize.

    Warnings:
        This is a crude way of scanning modules for routers.

    Yields:
        Entrypoint:
        Entrypoint object with router module and the bare name of it.
    """
    package = pathlib.Path(os.path.dirname(routers)).stem
    base_package = pathlib.Path(os.path.dirname(routers)).parent.stem
    for __path, __directory, __file in os.walk(routers):
        if __path.endswith("__"):
            continue
        for file_ in __file:
            if file_.startswith("__") or file_ == "favicon.ico":
                continue
            filepath = pathlib.PurePath(file_)
            if filepath.suffix == ".py":
                breaker = pathlib.PurePath(os.path.join(__path, filepath.stem)).parts
                # Replace paths with . to make it appear as a module
                # black formats to include space between '1' and ':', refer: https://github.com/psf/black/issues/1323
                yield Entrypoint(
                    module=".".join(
                        (base_package,) + breaker[breaker.index(package):]  # fmt: skip
                    ),
                    stem=filepath.stem,
                )


def routes(routers: str) -> Generator[APIRouter]:
    """Scans routers directory to import all the routers available.

    Args:
        routers: Directory name where the potential router modules are present.

    Yields:
        APIRouter:
        API Router from scanned modules.
    """
    # sort by name of the route
    entrypoints: List[Entrypoint] = sorted(
        get_entrypoints(routers=routers), key=lambda ent: ent.stem
    )
    for entrypoint in entrypoints:
        try:
            route = import_module(entrypoint.module)
        except ImportError as error:
            logger.error(error)
            warnings.warn(error.__str__())
            continue
        if hasattr(route, "router"):
            logger.info("Loading router: %s", entrypoint.module)
            yield getattr(route, "router")
        else:
            logger.warning("%s is missing the router attribute.", route.__name__)

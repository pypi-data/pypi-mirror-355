import atexit
import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import ClassVar, Type

from .config import BaseConfig, LoggerConfig
from .modules import BaseModule


class ModuBotCore(BaseConfig):
    NAME: ClassVar[str] = "ModuBotCore"
    VERSION: ClassVar[str] = "0.0.1"
    LOGGER_CONFIG: ClassVar[Type[LoggerConfig]] = LoggerConfig
    MODULE_BASE_CLASS: ClassVar[Type[BaseModule]] = BaseModule

    def __init__(self):
        logging.basicConfig(
            level=self.LOGGER_CONFIG.LEVEL,
            format=self.LOGGER_CONFIG.FORMAT,
            datefmt=self.LOGGER_CONFIG.DATEFMT,
        )
        self.modules: list[BaseModule] = []
        atexit.register(self.stop)

    def run(self):
        self.logger.info(f"Starting {self.NAME}")
        self._load_modules()
        for module in self.modules:
            self.logger.info(f'Enabling module "{module.NAME}"')
            module.on_enable()

    def stop(self):
        for module in self.modules:
            self.logger.info(f'Disabling module "{module.NAME}"')
            module.on_disable()
        self.logger.info(f"Stopping {self.NAME}")

    def _load_modules(self):
        root = Path().resolve()
        module_dir = root / "modules"
        self.logger.debug(f'Loading modules from "{module_dir}"')

        for mod_path in module_dir.iterdir():
            if not mod_path.is_dir():
                continue

            init_file = mod_path / "__init__.py"
            if not init_file.exists():
                continue

            module_name = f"modules.{mod_path.name}"
            spec = importlib.util.spec_from_file_location(module_name, init_file)
            if not spec or not spec.loader:
                continue

            mod = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)

            for item in dir(mod):
                obj = getattr(mod, item)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, self.MODULE_BASE_CLASS)
                    and obj is not self.MODULE_BASE_CLASS
                ):
                    if getattr(obj, "ENABLING", True):
                        self.logger.info(f'Loading module "{obj.NAME}"')
                        instance = obj()
                        self.modules.append(instance)
                    else:
                        self.logger.info(
                            f"Skipping module (ENABLING is False): {obj.NAME}"
                        )

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.NAME)

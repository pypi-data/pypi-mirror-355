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
    """
    Core class for the ModuBot framework.

    Handles logging, module loading, and lifecycle management (run/stop).
    Modules are expected to reside in the "modules" directory and inherit from the defined MODULE_BASE_CLASS.

    :cvar NAME: The name of the bot core.
    :cvar VERSION: Current version of the bot core.
    :cvar LOGGER_CONFIG: Logger configuration class.
    :cvar MODULE_BASE_CLASS: Base class for all modules to be loaded.
    """

    NAME: ClassVar[str] = "ModuBotCore"
    VERSION: ClassVar[str] = "0.0.1"
    LOGGER_CONFIG: ClassVar[Type[LoggerConfig]] = LoggerConfig
    MODULE_BASE_CLASS: ClassVar[Type[BaseModule]] = BaseModule

    def __init__(self):
        """
        Initializes logging and prepares the module list.

        Registers the stop() method to be called automatically on application exit.
        """
        logging.basicConfig(
            level=self.LOGGER_CONFIG.LEVEL,
            format=self.LOGGER_CONFIG.FORMAT,
            datefmt=self.LOGGER_CONFIG.DATEFMT,
        )
        self.modules: list[BaseModule] = []
        atexit.register(self.stop)

    def run(self):
        """
        Starts the bot and enables all loaded modules.

        Calls the on_enable() method of each module after loading.
        """
        self.logger.info(f"Starting {self.NAME}")
        self._load_modules()
        for module in self.modules:
            self.logger.info(f'Enabling module "{module.NAME}"')
            module.on_enable()

    def stop(self):
        """
        Disables all loaded modules and logs shutdown.

        Calls the on_disable() method of each module.
        """
        for module in self.modules:
            self.logger.info(f'Disabling module "{module.NAME}"')
            module.on_disable()
        self.logger.info(f"Stopping {self.NAME}")

    def _load_modules(self):
        """
        Dynamically loads all modules from the "modules" directory.

        Each module must be in its own directory with an `__init__.py` file.
        The module must contain a class that inherits from MODULE_BASE_CLASS.
        Only modules with ENABLING = True will be instantiated and added.
        """
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
        """
        Returns the logger instance for the bot.

        :return: Logger bound to the bot's NAME.
        :rtype: logging.Logger
        """
        return logging.getLogger(self.NAME)

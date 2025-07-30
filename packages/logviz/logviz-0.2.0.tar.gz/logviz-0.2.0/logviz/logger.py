import logging
from typing import Any, Dict, Optional

from logviz.defaults import DEFAULT_DATE_FORMAT, DEFAULT_EXCEPTION_STYLE, DEFAULT_LOG_FORMAT, DEFAULT_STYLES
from logviz.formatters import LogVizFormatter
from logviz.styles import LogLevelStyle


class LogVizLogger(logging.Logger):
    """
    A custom Logger class that automatically configures itself with a
    StreamHandler and a LogVizFormatter for colored console output.
    Allows for custom default style maps and per-message custom styling.
    """

    def __init__(self, name: str, level: int = logging.NOTSET,
                 style_map: Optional[Dict[int, LogLevelStyle]] = None):  # <-- NEW: Optional style_map
        super().__init__(name, level)

        # By default, don't propagate to the root logger, giving us full control.
        self.propagate = False

        # Use provided style_map or the default one from defaults.py
        self._logger_style_map = style_map if style_map is not None else DEFAULT_STYLES

        # Set up the default console handler with our custom formatter
        # Ensure we don't add duplicate StreamHandlers
        if not any(isinstance(h, logging.StreamHandler) for h in self.handlers):
            console_handler = logging.StreamHandler()

            # Instantiate our LogVizFormatter with the logger's style map
            formatter = LogVizFormatter(
                fmt=DEFAULT_LOG_FORMAT,
                datefmt=DEFAULT_DATE_FORMAT,
                default_style_map=self._logger_style_map,  # <-- Pass the logger's style map
                exception_style=DEFAULT_EXCEPTION_STYLE
            )
            console_handler.setFormatter(formatter)
            self.addHandler(console_handler)

        # Set the logger's level
        if level is not logging.NOTSET:
            self.setLevel(level)

    def _log_message(self, level: int, msg: str, exc_info: Any = None,
                     extra: Optional[Dict[str, Any]] = None,
                     custom_style: Optional[LogLevelStyle] = None,
                     *args, **kwargs):
        """
        Internal helper to log a message, potentially with custom styling
        and exception information.
        """
        if extra is None:
            extra = {}

        # If a custom style is provided, add it to the extra dict
        if custom_style:
            extra['_logviz_custom_style'] = custom_style

        # Call the parent logging.Logger's log method
        super().log(level, msg, *args, exc_info=exc_info, extra=extra, **kwargs)

    # --- Overridden standard logging methods to use our internal helper ---
    def debug(self, msg, *args, **kwargs):
        self._log_message(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log_message(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log_message(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log_message(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log_message(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """
        Logs a message with level ERROR, and adds exception information.
        This is a convenience method that calls error() with exc_info set to True.
        """
        # Ensure exc_info is True if not explicitly provided or is None
        kwargs['exc_info'] = True if 'exc_info' not in kwargs or kwargs['exc_info'] is None else kwargs['exc_info']
        self._log_message(logging.ERROR, msg, *args, **kwargs)

    def success(self, msg, *args, **kwargs):
        """
        Logs a message with the custom SUCCESS level.
        The style will be applied by the formatter based on the logger's default style map.
        """
        super().log(logging.SUCCESS, msg, *args, **kwargs)


def get_logger(name: str = "logviz", level: int = logging.NOTSET,
               style_map: Optional[Dict[int, LogLevelStyle]] = None) -> "LogVizLogger":
    """
    Returns a LogVizLogger instance, ensuring our custom logger class is used.
    This is the primary way users will get a logger from LogViz.
    Allows passing a custom style_map for this logger instance.
    """
    logging.setLoggerClass(LogVizLogger)
    logger = logging.getLogger(name)
    logging.setLoggerClass(logging.Logger)  # Reset to default logging.Logger

    if not isinstance(logger, LogVizLogger) or logger._logger_style_map != style_map:
        logger.__class__ = LogVizLogger
        logger.__init__(name, level, style_map)
    else:
        if level is not logging.NOTSET:
            logger.setLevel(level)

    return logger


# Example usage for direct execution of logger.py (for quick testing

logger = get_logger(level=logging.DEBUG)

# Example usage for direct execution of logger.py (for quick testing)

import logging

from logviz.styles import LogLevelStyle, Style

DEFAULT_DEBUG_STYLE = LogLevelStyle(foreground_color=Style.BRIGHT_BLACK, italic=True)
DEFAULT_INFO_STYLE = LogLevelStyle(foreground_color=Style.BLUE)
DEFAULT_WARNING_STYLE = LogLevelStyle(foreground_color=Style.YELLOW, bold=True)
DEFAULT_ERROR_STYLE = LogLevelStyle(foreground_color=Style.RED, bold=True, underline=False)
DEFAULT_CRITICAL_STYLE = LogLevelStyle(foreground_color=Style.ORANGE, bold=True, italic=True)
DEFAULT_EXCEPTION_STYLE = LogLevelStyle(foreground_color=Style.RED, bold=True, underline=True, italic=True)
DEFAULT_SUCCESS_STYLE = LogLevelStyle(foreground_color=Style.GREEN, bold=True)

logging.SUCCESS = 25
logging.addLevelName(logging.SUCCESS, 'SUCCESS')

DEFAULT_STYLES = {
    logging.DEBUG: DEFAULT_DEBUG_STYLE,
    logging.INFO: DEFAULT_INFO_STYLE,
    logging.WARNING: DEFAULT_WARNING_STYLE,
    logging.ERROR: DEFAULT_ERROR_STYLE,
    logging.CRITICAL: DEFAULT_CRITICAL_STYLE,
    logging.SUCCESS: DEFAULT_SUCCESS_STYLE,
}

DEFAULT_LOG_FORMAT = "%(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

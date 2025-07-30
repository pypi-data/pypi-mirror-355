# logviz/logviz/formatters.py

import logging
from logviz.styles import Style, LogLevelStyle
from logviz.defaults import DEFAULT_STYLES, DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT, DEFAULT_EXCEPTION_STYLE


class LogVizFormatter(logging.Formatter):
    """
    A custom logging formatter that applies ANSI escape codes for colors and styles.
    It prioritizes per-record custom styles passed via `extra`, then falls back
    to logger-configured default styles, and finally handles exception tracebacks.
    """

    def __init__(self, fmt: str = DEFAULT_LOG_FORMAT,
                 datefmt: str = DEFAULT_DATE_FORMAT,
                 default_style_map: dict = None,  # <-- Renamed for clarity: this is the logger's default
                 exception_style: LogLevelStyle = DEFAULT_EXCEPTION_STYLE):
        super().__init__(fmt, datefmt)
        self.default_style_map = default_style_map if default_style_map is not None else DEFAULT_STYLES
        self.exception_style = exception_style

        # Define a key for finding custom styles in record.extra
        self._CUSTOM_STYLE_KEY = '_logviz_custom_style'

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record and applies styling, including for exceptions.
        Prioritizes a custom style provided in record.extra.
        """
        # --- Handle exception traceback (exc_info=True) ---
        # Temporarily clear exc_info so super().format() doesn't include it
        # We will format and style the traceback separately.
        exc_text_original = record.exc_text
        exc_info_original = record.exc_info
        record.exc_text = None
        record.exc_info = None

        # --- Determine the style to apply for the current record ---
        # 1. Check for a custom style explicitly passed for this record
        current_style = getattr(record, self._CUSTOM_STYLE_KEY, None)

        # 2. If no custom style, fall back to the default style for the log level
        if current_style is None:
            current_style = self.default_style_map.get(record.levelno)

        # Get the raw, uncolored formatted message from the parent formatter
        # This uses the fmt string (e.g., "%(levelname)s - %(message)s")
        formatted_message = super().format(record)

        # Apply base styling (colors, bold, casing) to the main message part
        final_message = formatted_message  # Start with unstyled message

        if current_style:
            # Apply casing to the *entire* formatted message string
            cased_message = current_style.apply_casing(formatted_message)
            # Apply ANSI escape codes to the entire cased message
            final_message = f"{current_style.get_ansi_codes()}{cased_message}{Style.RESET}"

        # --- Append styled exception traceback if present ---
        if exc_info_original:
            # Re-set exc_info on the record for super().formatException to work
            record.exc_info = exc_info_original
            # Get the raw formatted traceback string
            formatted_traceback = self.formatException(exc_info_original)

            if formatted_traceback:
                # Apply the dedicated exception style to the traceback
                styled_traceback = self.exception_style.apply_casing(formatted_traceback)
                styled_traceback = f"{self.exception_style.get_ansi_codes()}{styled_traceback}{Style.RESET}"

                # Append the styled traceback to the main message
                final_message += f"\n{styled_traceback}"

        # Restore original exc_text/exc_info for potential other handlers down the chain
        record.exc_text = exc_text_original
        record.exc_info = exc_info_original

        return final_message



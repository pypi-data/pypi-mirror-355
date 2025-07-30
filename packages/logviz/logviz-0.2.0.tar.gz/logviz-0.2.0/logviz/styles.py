class Style:
    """
    ANSI escape codes for basic text styling (colors, bold, etc.).
    These are standard codes supported by most modern terminals.
    """
    RESET = "\033[0m"  # Reset all attributes

    # --- Text Attributes ---
    BOLD = "\033[1m"
    DIM = "\033[2m"  # Less pronounced than normal
    ITALIC = "\033[3m"  # Not widely supported in all terminals
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"  # Often not supported or ignored
    REVERSE = "\033[7m"  # Swap foreground and background
    HIDDEN = "\033[8m"  # Not widely supported
    STRIKETHROUGH = "\033[9m"  # Not widely supported

    # --- Foreground Colors (8-color mode) ---
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    ORANGE = "\033[38;5;166m"

    # --- Bright Foreground Colors (often 16-color mode) ---
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # --- Background Colors (8-color mode) ---
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # --- Bright Background Colors (often 16-color mode) ---
    BG_BRIGHT_BLACK = "\033[100m"
    BG_BRIGHT_RED = "\033[101m"
    BG_BRIGHT_GREEN = "\033[102m"
    BG_BRIGHT_YELLOW = "\033[103m"
    BG_BRIGHT_BLUE = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN = "\033[106m"
    BG_BRIGHT_WHITE = "\033[107m"

    @staticmethod
    def rgb_fg(r: int, g: int, b: int) -> str:
        """Returns ANSI code for 24-bit foreground color."""
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def rgb_bg(r: int, g: int, b: int) -> str:
        """Returns ANSI code for 24-bit background color."""
        return f"\033[48;2;{r};{g};{b}m"

    @staticmethod
    def eight_bit_fg(code: int) -> str:
        """Returns ANSI code for 8-bit foreground color (0-255)."""
        return f"\033[38;5;{code}m"

    @staticmethod
    def eight_bit_bg(code: int) -> str:
        """Returns ANSI code for 8-bit background color (0-255)."""
        return f"\033[48;5;{code}m"


class LogLevelStyle:
    """
    Defines the visual styling for a specific logging level.

    Attributes:
        foreground_color (str): ANSI code for text color (e.g., Style.RED, or Style.rgb_fg(255,0,0)).
        background_color (str): ANSI code for background color (e.g., Style.BG_BLUE).
        bold (bool): Apply bold text attribute.
        dim (bool): Apply dim text attribute.
        italic (bool): Apply italic text attribute.
        underline (bool): Apply underline text attribute.
        strikethrough (bool): Apply strikethrough text attribute.
        reverse (bool): Apply reverse (swap FG/BG) attribute.
        hidden (bool): Apply hidden attribute.
        uppercase (bool): Convert message to UPPERCASE.
        lowercase (bool): Convert message to lowercase.
        capitalize (bool): Capitalize the first letter of the message.
        font_size (str): Placeholder for desired font size (not directly supported by ANSI).
                         Could be used for integration with UI libraries or specific terminal emulators.
                         Example: "small", "medium", "large"
    """

    def __init__(self,
                 foreground_color: str = None,
                 background_color: str = None,
                 bold: bool = False,
                 dim: bool = False,
                 italic: bool = False,
                 underline: bool = False,
                 strikethrough: bool = False,
                 reverse: bool = False,
                 hidden: bool = False,
                 uppercase: bool = False,
                 lowercase: bool = False,
                 capitalize: bool = False,
                 font_size: str = None):  # Terminal font size is generally not controllable via ANSI

        self.foreground_color = foreground_color
        self.background_color = background_color
        self.bold = bold
        self.dim = dim
        self.italic = italic
        self.underline = underline
        self.strikethrough = strikethrough
        self.reverse = reverse
        self.hidden = hidden
        self.uppercase = uppercase
        self.lowercase = lowercase
        self.capitalize = capitalize
        self.font_size = font_size  # This attribute is for potential future use or integration with other tools

    def get_ansi_codes(self) -> str:
        """
        Returns a string of combined ANSI escape codes for the defined style.
        """
        codes = []
        if self.foreground_color:
            codes.append(self.foreground_color)
        if self.background_color:
            codes.append(self.background_color)
        if self.bold:
            codes.append(Style.BOLD)
        if self.dim:
            codes.append(Style.DIM)
        if self.italic:
            codes.append(Style.ITALIC)
        if self.underline:
            codes.append(Style.UNDERLINE)
        if self.strikethrough:
            codes.append(Style.STRIKETHROUGH)
        if self.reverse:
            codes.append(Style.REVERSE)
        if self.hidden:
            codes.append(Style.HIDDEN)

        return "".join(codes)

    def apply_casing(self, text: str) -> str:
        """
        Applies casing transformation to the text based on style settings.
        """
        if self.uppercase:
            return text.upper()
        elif self.lowercase:
            return text.lower()
        elif self.capitalize:
            # Capitalize only the first letter of the *message part* if the format string allows
            # This is a basic capitalization. More robust handling might be needed in formatter.
            return text.capitalize()
        return text

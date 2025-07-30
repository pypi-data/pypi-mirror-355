# README.md

# README #

LogViz: A Python logging library for colorful and styled console output.

### Programmer ###
* Owusu Kenneth Gyamfi [okwesi]

### Contributors ###
* No Contributors currently, but feel free to contribute!

### Contribution guidelines ###
* Use present perfect tense to comment all code. e.g., "Create a user."
* Follow PEP8 for code formatting.
* Run tests via `pytest`.

## Naming conventions
* Module and variable names: lowercase_with_underscores.
* Class names: CapWords.
* Constants: UPPERCASE_WITH_UNDERSCORES.

### Requirements ###
- Python 3.6+
- No external dependencies beyond the standard library.

### Installation ###
    pip install logviz

### Usage ###
    from logviz import logger

    if __name__ == "__main__":
        logger.debug("This is a debug message.")
        logger.info("This is an info message.")
        logger.success("This is a success message.")
        logger.warning("This is a warning message.")
        logger.error("This is an error message.")
        logger.critical("This is a critical message.")
        try:
            1/0
        except ZeroDivisionError:
            logger.exception("This is an exception message: Division by zero error occurred!")

#### Example Output ####
![FCOJt5u.md.png](https://iili.io/FCOJt5u.md.png)

### API Reference ###
- `get_logger(name: str = "logviz", level: int = logging.NOTSET) -> LogVizLogger`
- Logging methods:
  - `logger.debug(msg: str)`
  - `logger.info(msg: str)`
  - `logger.success(msg: str)`
  - `logger.warning(msg: str)`
  - `logger.error(msg: str)`
  - `logger.critical(msg: str)`
  - `logger.exception(msg: str)`


### Project Structure ###
    logviz/
    └── logviz/
        ├── __init__.py
        ├── defaults.py
        ├── formatters.py
        ├── logger.py
        └── styles.py

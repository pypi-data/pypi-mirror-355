# Built-in Modules
import typing
import logging
import datetime as dt


# Local Modules
from quantsapp import constants as generic_constants

# -- Default Logger ----------------------------------------------------------------------------------

# Convert timesystem to IST
logging.Formatter.converter = lambda *args: dt.datetime.now(generic_constants.DT_ZONE_IST).timetuple()  # type:ignore


__RESET = '\033[0m'
__BOLD = '\033[1m'
__BLINK = '\033[5m'
__GREY = '\033[90m'
__RED = '\033[31m'
__GREEN = '\033[32m'
__YELLOW = '\033[33m'

__colors = {
    logging.DEBUG: __GREY,
    logging.INFO: __GREEN,
    logging.WARNING: __YELLOW,
    logging.ERROR: __RED,
    logging.CRITICAL: __RED + __BOLD + __BLINK,
}

DEFAULT_FORMATTER = logging.Formatter(
    fmt=f"[%(asctime)s.%(msecs)3d] [%(name)s-%(levelname)s] [%(filename)s.%(lineno)d-%(threadName)s-%(funcName)s()]:- %(message)s",
    datefmt='%d%b%y %H:%M:%S',
)


class ColorFormatter(logging.Formatter):
    """
        Coloring Logs based on level for easy identification

        Ref - https://stackoverflow.com/a/77032543/13029007
    """

    def __init__(self, *args: typing.Any, colors: dict[int, str], **kwargs: typing.Any):
        super().__init__(*args, **kwargs)

        replace_tags = lambda level: self._style._fmt.replace("#color", colors.get(level, "")) # type: ignore
        levels = set(logging.getLevelNamesMapping().values())
        self._fmts = {
            level: replace_tags(level)
            for level in levels
        }

    def format(self, record: logging.LogRecord):
        self._style._fmt = self._fmts.get(record.levelno) # type: ignore
        return super().format(record)


stream_handler = logging.StreamHandler()
stream_handler.setFormatter(
    ColorFormatter(
        fmt=f"#color[%(asctime)s.%(msecs)3d] [%(name)s-%(levelname)s] [%(filename)s.%(lineno)d-%(threadName)s-%(funcName)s()]:-{__RESET} %(message)s",
        datefmt='%d%b%y %H:%M:%S',
        colors=__colors,
    )
)


qapp_logger = logging.getLogger('quantsapp')
qapp_logger.setLevel(logging.ERROR)
qapp_logger.addHandler(stream_handler)

# -- Stream Handler ----------------------------------------------------------------------------------

# TODO try to add options for file handler also
def _set_stream_logger(
        level: int = logging.ERROR,
        format_string: typing.Optional[str] = None,
    ):
    """ TODO change the description
    Add a stream handler for the given name and level to the logging module.
    By default, this logs all Quantsapp messages to ``stdout``.

    >>> import quantsapp
    >>> quantsapp._logger._set_stream_logger(logging.INFO)

    # :type name: string
    # :param name: Log name
    :type level: int
    :param level: Logging level, e.g. ``logging.INFO``
    :type format_string: str
    :param format_string: Log message format
    """

    global qapp_logger

    qapp_logger.setLevel(level)

    if format_string:
        formatter = logging.Formatter(
            fmt=format_string,
            datefmt='%d%b%y %H:%M:%S',
        )
        qapp_logger.handlers[0].setFormatter(
            fmt=formatter,
        )

# -- File Handler ------------------------------------------------------------------------------------

def _set_file_logger(
        file_path: str,
        mode: str = 'a',
        format_string: typing.Optional[str] = None,
    ):
    """ TODO change the description
    Add a stream handler for the given name and level to the logging module.
    By default, this logs all Quantsapp messages to ``stdout``.

    >>> import quantsapp
    >>> quantsapp._logger._set_file_logger(file='quantsapp', logging.INFO)
    """

    fileHandler = logging.FileHandler(
        filename=file_path,
        mode=mode,
    )

    if format_string:
        _formatter = logging.Formatter(
            fmt=format_string,
            datefmt='%d%b%y %H:%M:%S',
        )
    else:
        _formatter = DEFAULT_FORMATTER

    fileHandler.setFormatter(_formatter)
    qapp_logger.addHandler(fileHandler)


# def set_logging_handlers():

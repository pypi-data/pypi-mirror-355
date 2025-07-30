from __future__ import annotations

import datetime
import logging
import os
from typing import Optional

# ---------------------------------------------------------------------------
# Internal helper – ensures each library logger has ONE NullHandler so that
# importing AIgent never emits warnings if the host app hasn't configured
# logging yet.
# ---------------------------------------------------------------------------

_NULL_HANDLER = logging.NullHandler()


def _ensure_null_handler(logger: logging.Logger) -> None:

    # Attach a *NullHandler* once to the given logger (idempotent).
    if not any(isinstance(h, logging.NullHandler) for h in logger.handlers):
        logger.addHandler(_NULL_HANDLER)
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a library‑style logger.

    Parameters
    ----------
    name : str | None
        Logger name; defaults to the caller's module name (when ``None``).
    Returns
    -------
    logging.Logger
        A logger with a *NullHandler* attached, so it won't complain if the application hasn't set up logging yet.
    """

    logger = logging.getLogger(name)
    _ensure_null_handler(logger)
    logger.propagate = True  # Ensure logs propagate to parent loggers
    return logger

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
def setup_logging(
    level: str = "INFO",
    logfile: Optional[str] = None,
    fmt: str = "%(asctime)s %(levelname)-8s - %(name)-32s:%(lineno)-5s  - %(message)s",
    datefmt: str = "%Y-%m-%d %H:%M:%S",
) -> None:
    """
    Configure the root logger with a handler and specified format.

    Parameters
    ----------
    level : str
        Logging level name (e.g. "INFO", "DEBUG").
    logfile : Optional[str]
        Path to a log file. If None, logs are emitted to stderr.
    fmt : str
        Log message format.
    datefmt : str
        Date/time format.
    """
    root = logging.getLogger()
    if root.handlers:
        return
    if logfile:
        try:
            if os.path.exists(logfile):
                ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                os.rename(logfile, f"{logfile}.{ts}")
        except Exception as e:
            # Failed to rotate existing log file; continue with fresh log
            print(f"Failed to rotate log file {logfile}: {e}", file=sys.stderr)
    handler = logging.FileHandler(logfile) if logfile else logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt=fmt, datefmt=datefmt))
    root.addHandler(handler)
    root.setLevel(level.upper())


# ---------------------------------------------------------------------------
# When executed directly – a simple smoke test that respects whatever logging
# the **application** (or user) has configured.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    # If the user launched this file directly, configure a temporary basic
    # stream handler so they see output.
    if not logging.getLogger().handlers:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.DEBUG,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    log = get_logger(__name__)
    log.debug("Debug message from AIgent logger test harness")
    log.info("Info message")
    log.warning("Warning message")
    log.error("Error message")
    log.critical("Critical message")

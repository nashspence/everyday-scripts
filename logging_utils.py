import atexit, logging, os, sys, time
from datetime import datetime, timezone

def setup_logging(logfile: str, name: str | None = None) -> logging.Logger:
    """
    Configure root logger so every script logs the same way.
    Writes to `logfile` *and* to stderr (so the tailing Terminal shows live output).
    """
    logger = logging.getLogger(name)
    if logger.hasHandlers():                             # avoid duplicate handlers
        logger.handlers.clear()

    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s ▶ %(levelname)s ▶ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S UTC",
    )
    # always stamp in UTC
    logging.Formatter.converter = lambda *args: time.gmtime(*args)

    fh = logging.FileHandler(logfile)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    logger.info("Script started")
    atexit.register(lambda: logger.info("Script exited"))
    return logger


def prepend_path():
    # Match the PATH changes in your original script
    os.environ["PATH"] = "/opt/homebrew/bin:/usr/local/bin:" + os.environ["PATH"]

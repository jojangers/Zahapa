"""
Entry point for zahapa

python -m zahapa
"""
from .cli import main
from .logger import Logger
import logging

if __name__ == "__main__":
    logging.setLoggerClass(Logger)
    try:
        status = main()
    except:
        Logger.critical("shutting down due to fatal error")
        raise
    else:
        raise SystemExit(status)
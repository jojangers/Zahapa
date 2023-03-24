"""
Global logging application

"""

from logging import Formatter
from logging import Logger as _Logger
from logging import NullHandler
from logging import StreamHandler
__all__ = "logger", "Logger"

class Logger(_Logger):
    """ Message logger.
    
    """
    LOGFMT = '%(asctime)s;%(levelname)s;[%(name)s];%(message)s'
    
    def __init__(self, name=None):
        """Initialise this logger.add()

        Args:
            name (str, optional): Logger name (application name by default)
        """
        super(Logger, self).__init__(name or __name__.split(".")[0])
        self.addHandler(NullHandler()) # Default to no output
        
    def start(self, level="INFO", stream=None):
        """start logging to a stream.
        
        Until the logger is started, no messages will be emitted. This applies
        to all loggers with the same name and any child loggers.
        
        Multiple Streams can be logged to by calling start() for each one.
        Calling start() more than once for the same stream will result in
        duplicate records to that stream.

        Args:
            level (str, optional): logger priority level. Defaults to "WARN".
            stream (str, optional): output stream. Defaults to stdout.
        """
        self.setLevel(level.upper())
        handler = StreamHandler(stream)
        handler.setFormatter(Formatter(self.LOGFMT))
        handler.setLevel(self.level)
        self.addHandler(handler)
        return
        
    def stop(self):
        for handler in self.handlers[1:]:
            # remove everything except NullHandler.
            self.removeHandler(handler)
        return
logger = Logger()
"""
CLI interface for zahapa.
"""
import os
import yaml
import gevent
import signal
import systemd
import logging
import argparse
from . import __version__
from .logger import Logger
from .database import db_monitor
from .webserver import zahapa_webserver

__all__ = "main",

# TODO: change yaml loading to .ini file for cleaner code and config file.
# TODO: make systemd package install work
# TODO: notify systemd of startup completion.
# TODO: provide correct exit code.
# TODO: add checking of greenlet status and auto restart if failed
# TODO: add config reload functionality.


# add easy start and stop functions to logger class.
logging.setLoggerClass(Logger)
logger = logging.getLogger(__name__.split(".")[0])

def main():
    # load commandline arguments
    args = _setup_args()
    # start logging to stdout
    logger.start(args.loglevel)
    
    #logger.addHandler(journal.JournaldLogHandler())
    logger.info('starting execution')
    # load config file
    config = _load_configuration(args.config)
    
    
    
    
    # DB monitor config
    db_host     = config.get('db_host', "localhost")
    db_password = config.get('db_password', '')
    db_name     = config.get('db_name', "zabbix")
    db_user     = config.get('db_user', 'zahapa')
    db_port     = config.get('db_port', "3306")
    node_name   = config.get('zbx_node_name', os.getenv('HOSTNAME'))
    interval    = config.get('monitor_interval', '5')
    
    db_greenlet = db_monitor(
        db_name = db_name,
        db_host = db_host,
        db_port = db_port,
        db_user = db_user,
        db_password = db_password,
        zbx_node_name = node_name,
        interval = interval
        )
    
    webserver = zahapa_webserver(
        bind = config.get('bind', "0.0.0.0"),
        port = config.get('port', 5555),
        response = db_greenlet.get
    )
    
    
    # setup handlers to ensure clean closure on exit.
    setup_handlers(db_greenlet.stop)
    setup_handlers(webserver.stop_webserver)
    
    
    # run the db query function
    webserver.start_webserver()
    db_greenlet.run()
        
    gevent.wait()
    

def setup_handlers(function) -> None:
    """
    - if SIGTERM is received, shut down and exit cleanly.
    - if SIGHUP is received, reload the configuration files.
    """
    gevent.signal_handler(signal.SIGINT, function)
    gevent.signal_handler(signal.SIGTERM, function)    

def _load_configuration(config_file) -> dict:
    try:
        # load config file as yaml
        with open(config_file) as config_fd:
            # add config dictionary to "config" variable
            config = yaml.load(config_fd, Loader=yaml.SafeLoader)
        logger.debug('Loaded config: %s', config)
        return config
    except OSError as err:
        logger.critical('Failed to open config file: %s', err)
        raise SystemExit(1) from err
  
def _setup_args():
    parser = argparse.ArgumentParser(description="zahapa service")
    parser.add_argument("-c", "--config",
                        default="/etc/zahapa/config.yml",
                        type=str,
                        help="path to yaml configuraion file")
    parser.add_argument("-l", "--loglevel",
                        default='info',
                        choices=['info', 'warn', 'debug', 'critical'],
                        type=str,
                        help="set logging level")
    parser.add_argument("-v", "--version", 
                        action="version",
                        version=__version__)

    return parser.parse_args()
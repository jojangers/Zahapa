#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Owner: Jojangers <jojangers@gmail.com>
# Version: 1.0.0

###########
# Imports #
###########
from gevent import monkey
monkey.patch_all()

import os
import sys
import signal
import argparse
from functools import partial
import gevent
from gevent.server import StreamServer
import yaml
import mysql.connector






#############
# arguments #
#############
parser = argparse.ArgumentParser(description="zahapa service")
parser.add_argument("-c", "--config",
                    default="/opt/zahapa/config.yml",
                    type=str,
                    help="path to yaml configuraion file")
parser.add_argument("-l", "--loglevel",
                    default='info',
                    choices=['info', 'warn', 'debug', 'critical'],
                    type=str,
                    help="set logging level")

args = parser.parse_args()


#############
# Functions #
#############

def setup_logger(args):
    # import inside function to fix bug
    import logging
    # Create
    global logger
    # set level of logs from commandline arguments
    loglevel = args.loglevel.upper()
    # set logging format
    logformat = '%(asctime)s %(levelname)s [%(name)s] %(message)s'

    # configure logging function.
    logging.basicConfig(format=logformat, level=loglevel)
    logger = logging.getLogger('zahapa')
    
    if not sys.platform == "linux":
        import logging.handlers
        handler = logging.handlers.SysLogHandler(address='/dev/log')
        logger.addHandler(handler)
        

## CONFIG

def load_configuration(config_file):
    # load config file as yaml
    with open(config_file) as config_fd:
        # add config dictionary to "config" variable
        config = yaml.load(config_fd, Loader=yaml.SafeLoader)
    logger.debug('config is {}'.format(config))
    # return config dictionary
    return config

    
"""
status number definitions from zabbix source code:
#define ZBX_NODE_STATUS_HATIMEOUT	-3
#define ZBX_NODE_STATUS_ERROR		-2
#define ZBX_NODE_STATUS_UNKNOWN		-1
#define ZBX_NODE_STATUS_STANDBY		0
#define ZBX_NODE_STATUS_STOPPED		1
#define ZBX_NODE_STATUS_UNAVAILABLE	2
#define ZBX_NODE_STATUS_ACTIVE		3
"""
def zabbix_ha_status(hostname):
    try:
        status = "none"
        db_cursor = db_connection.cursor()
        query = ("SELECT name, status FROM ha_node WHERE name like '{}'")
        
        logger.debug("executing query: {}".format(query.format(hostname)))
        db_cursor.execute(query.format(hostname))
        
        logger.debug("entire db_cursor store: {}".format(db_cursor))
        for name, status in db_cursor:
            logger.debug("got results: name: {} status: {}".format(str(name), status))
            if status == 0:
                # since standby mode does nto accept connections but server is up, set to maintenance mode.
                status = "up maint"
            elif status == 3:
                # ready to make sure server is not in maintenance mode and up to make sure server is marked as accessible.
                status = "ready up"
            else:
                status = "down"
        logger.info("returning %s", status)
        db_cursor.close()
        return status
        
    except mysql.connector.Error as e:
        db_cursor.close()
        logger.critical("Error retrieving entry from database: {}".format(e))
        sys.exit(1)
        
        

        

## SERVER

def handle_requests(socket, addr):
    # log to debug
    logger.debug("received connect from {}".format(addr))
    query = config.get('zbx_node_name', os.getenv('HOSTNAME'))
    # recieve text from haproxy
    zabbix_status = zabbix_ha_status(query)
    # log to debug
    logger.debug("writing state: {}".format(zabbix_status))
    # send the response to haproxy
    response = str(zabbix_status)+"\n"
    socket.send(response.encode())
    

def start_server(config):
    # add port and bind address to "listen" variable.
    listen = (config.get('bind', '0.0.0.0'), int(config.get('port', '5555')))
    logger.debug("binding on address: {} on port: {}".format(listen[0], listen[1]))
    # start Streamserver on address and port (listen variable)
    # every connection will spawn a greenlet running the "handle_requests" function
    server = StreamServer(listen, handle_requests)
    
    # log event when start listening.
    logger.info("started listening{}".format(listen))
    # start the listening server
    server.start()
    # return server object
    return server

def start_database(config):
    # get variables from config
    db_host=config.get('db_host', "localhost")
    db_password=config.get('db_password')
    db_name=config.get('db_name', "zabbix")
    db_user=config.get('db_user')
    db_port=config.get('db_port', "3306")
    db_autocommit=True
    
    logger.info("started db connection on host:{} with database: {}".format(db_host, db_name))
    # setup database connection
    try:
        db_connection = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name,
        port=db_port,
        autocommit=db_autocommit
        )
    except mysql.connector.Error as e:
        logger.critical("Error retrieving entry from database: {}".format(e))
        sys.exit()
    db_connection.autocommit = True
    return db_connection
    



def setup_handlers(server, database):
    # setup handlers to close server and database connection gracefully.
    gevent.signal(signal.SIGINT, partial(stop_services, server, database))
    gevent.signal(signal.SIGTERM, partial(stop_services, server, database))


def stop_services(server, database):
    # create variable to keep track of server stopping
    global SERVER_STOPPING
    # check if stop is already in progress
    if not SERVER_STOPPING:
        SERVER_STOPPING = True
        # stop the server
        logger.info('stopping server')
        server.stop()
        # close database connection.
        logger.info('closing database connection')
        database.close()
    else:
        logger.info('stop is already in progress')

################
# Initialising #
################

# setup logging
setup_logger(args)

# load config file from commandline arguments
config = load_configuration(args.config)

# create variable to track server stopping
SERVER_STOPPING = False

##########
# Script #
##########


# start the server with args, config and plugins
db_connection = start_database(config)
server = start_server(config)

# setup the request handlers
setup_handlers(server, db_connection)
gevent.wait()
    

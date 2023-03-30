#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Owner: Jojangers <jojangers@gmail.com>
import logging
import mysql.connector
import os
import gevent

__all__ = "db_monitor"

# TODO: add proper exceptions to close the greenlet on failure.
# TODO: add methods to check greenlet status.
# TODO: add handling for query response containing more than one row
# TODO: add handling for no host found in query
# TODO: add checking to ensure only 1 greenlet is spawned incase "run" function is called multiple times.

#logging.setLoggerClass(Logger)
logger = logging.getLogger(__name__)


class db_monitor:
    def __init__(self, 
                db_name: str = "Zabbix", 
                db_host: str = "localhost", 
                db_port: int = 3306, 
                db_user: str = "zahapa", 
                db_password: str = "", 
                zbx_node_name: str = os.getenv('HOSTNAME'), 
                interval: int = 0,
                stop_timeout: int = 5):
        
        self.zbx_node_name = zbx_node_name
        self.interval = interval
        self.stop_timeout = stop_timeout

        # track if greenlet is currently shutting down.
        self.stopping = False

        # set default value to "down"
        self.value = "down"
        # set prepared query as constant.
        self.PREPARED_QUERY = "SELECT name, status FROM ha_node WHERE name like %s"

        # setup db_connection and prepared_cursor
        self.db_connection = self._connect_to_db(db_host, db_user, db_password, db_name, db_port)
        self.prepared_cursor = self._initialise_db_cursor(self.db_connection, self.PREPARED_QUERY)
    
    def run(self):
        """runs the monitor
        If interval is set, starts running query on an interval.
        if no interval is set, run query once and return result.

        Returns:
            str: current ha status.
        """
        if self.interval != 0:
            logger.debug(
                "running DB monitor with interval %s", self.interval
                )
            self.g = gevent.spawn(self.run_with_interval())
        else:
            logger.debug("running single DB query")
            output = self.query_ha_status()
            self.stop()
            return output
        
    def stop(self) -> None:
        """
        close connections gracefully.
        """
        if self.interval == 0:
            self.prepared_cursor.close()
            self.db_connection.close()
            return
        
        if self.stopping:
            logger.info('stop already in progress')

        else:
            logger.info('closing connections')
            try:
                timer = gevent.Timeout(self.stop_timeout)
                timer.start()
                self.stopping = True
                self.prepared_cursor.close()
                self.db_connection.close()
                self.g.join()
            except gevent.Timeout:
                logger.critical('could not stop within stop_timeout %s, terminating with kill.', self.stop_timeout)
                self.g.kill()
            finally:
                timer.cancel()
                return
            
    def run_with_interval(self) -> None:
        """
        Runs the ha query on set interval, updates value and calls gevent.sleep
        """
        while self.stopping == False:
            try:
                self.value = self.query_ha_status()
            except Exception as e:
                logger.critical('failed to query ha status, error: %s', e)
                raise e
            gevent.sleep(self.interval)

    
    def query_ha_status(self) -> str:
        try:
            logger.debug(f"executing query {self.PREPARED_QUERY} {self.zbx_node_name}")
            self.prepared_cursor.execute(self.PREPARED_QUERY, (self.zbx_node_name,))
            logger.debug(f"entire db_response: {self.prepared_cursor}")
            for name, status in self.prepared_cursor:
                logger.debug(f"got results: name: {str(name)} status: {status}")
                status = self._parse_ha_status(status)
            logger.debug("returning %s", status)
            return status
        except mysql.connector.Error as e:
            logger.critical(f"Error retrieving entry from database: {e}")
            raise e
    
    def __str__(self) -> str:
        """
        set current status to string value.

        Returns:
            str: current ha status
        """
        return str(self.value)
    
    def get(self) -> str:
        return str(self.value)
    
    @staticmethod
    def _connect_to_db(db_host: str, db_user: str, db_password: str, db_name: str, db_port: int) -> mysql.connector:
        """Sets up the connection to the DB for status queries.

        Returns:
            mysql.connector.connect: database connection
        """
        DBAUTOCOMMIT = True
        logger.info(
            f"starting db connection on host: {db_host} on database: {db_name}"
        )
        try:
            return mysql.connector.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                database=db_name,
                port=db_port,
                autocommit=DBAUTOCOMMIT,
            )
        except mysql.connector.Error as err:
            logger.critical("Error connecting to database: %s", err)
            raise err
    
    @staticmethod
    def _initialise_db_cursor(db_connection, query):
        """
        initialises the sql cursor with a prepared query.

        Args:
            db_connection (mysql.connector.connect): the DB connection
            query (String): prepared query

        Returns:
            sql_preparedcursor: prepared sql cursor
        """
        logger.debug(f"preparing query: {query}")
        try:
            db_cursor = db_connection.cursor(prepared=True)
            db_cursor.execute(query)
            return db_cursor
        except mysql.connector.Error as err:
            logger.critical("Error initalising prepared query: %s", err)
            raise err
    
    @staticmethod
    def _parse_ha_status(ha_status) -> str:
        """
        converts numerical status to haproxy response

        Args:
            ha_status (int): node status in db

        Returns:
            str: response for haproxy.

        status number definitions from zabbix source code:
        - -3  HA timed out      (ZBX_NODE_STATUS_HATIMEOUT)  
        - -2  node Error        (ZBX_NODE_STATUS_ERROR)  
        - -1  status unkown     (ZBX_NODE_STATUS_UNKNOWN)  
        - 0   standby node      (ZBX_NODE_STATUS_STANDBY)  
        - 1   node stopped      (ZBX_NODE_STATUS_STOPPED)
        - 2   node unavailable  (ZBX_NODE_STATUS_UNAVAILABLE)
        - 3   master node       (ZBX_NODE_STATUS_ACTIVE)
        """
        if ha_status == 0:
            # since standby mode does not accept connections but server is up,
            # set to maintenance mode.
            return "up maint"
        elif ha_status == 3:
            # "ready" to mark server out of maintenance mode.
            # "up" to mark server as accessible.
            return "ready up"
        else:
            # All other values should not be considered active.
            return "down"
        
    # method aliases
    start = run
    close = stop

        


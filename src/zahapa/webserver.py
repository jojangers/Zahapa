#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Owner: Jojangers <jojangers@gmail.com>

from . import __version__
from gevent.server import StreamServer
import logging

__all__ = "zahapa_webserver"

# TODO: only add newline to response if it does not exist already.
# TODO: add config option to serve the response on a specific url instead of '/'

#logging.setLoggerClass(Logger)
logger = logging.getLogger(__name__)


class zahapa_webserver:
    def __init__(self,
                 bind: str = "0.0.0.0",
                 port: int = 5555,
                 response: callable = None
                 ):
        
        self.bind = bind
        self.port = port
        
        # i dont like how this is done at all, but i dont know any better way currently.
        self.response = response
        
        logger.debug("response type is: %s", type(response))
        logger.debug("response value is: %s", response)
        
        self.server = self._init_webserver(bind, port)
    
    def start_webserver(self):
        self.server.start()
        logger.info(f"started listening on {self.bind}:{self.port}")
        return self.server
    
    def stop_webserver(self):
        logger.debug("stopping Streamserver")
        self.server.stop()
    
    def _init_webserver(self, bind, port) -> StreamServer:
        listen = (bind, port)
        logger.debug(f"binding on address: {listen[0]} on port: {listen[1]}")
        return StreamServer(listen, self._handle_web_requests)
        
    def _handle_web_requests(self, socket, addr) -> None:
        # call the "response" function to fetch the data.
        status = str(self.response())
        logger.debug(f"received connect from {addr}")
        logger.debug(f"writing state: {status}")
        # add a newline to the response as haproxy expects it.
        response = status if status.endswith("\n") else status+"\n"
        socket.send(response.encode())
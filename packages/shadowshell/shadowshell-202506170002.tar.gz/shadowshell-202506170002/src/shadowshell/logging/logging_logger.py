#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ConsoleLogger

author: shadow shell
"""

import logging
from .logger import Logger

class LoggingLogger(Logger):

    def debug(self, content):
        logging.debug(content)
    def info(self, content):
        logging.info("\n-->>")
        logging.info(content)

    def warn(self, content):
        logging.warn(content)
    
    def error(self, content):
        logging.error(content)


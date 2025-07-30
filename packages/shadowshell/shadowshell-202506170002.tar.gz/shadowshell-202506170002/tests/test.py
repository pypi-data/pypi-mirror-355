#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

@author: shadowshell
"""

from base_test import BaseTest
from src.shadowshell.xyz import Xyz
from src.shadowshell.logging import LoggerFactory

Xyz()

LoggerFactory.get_logger().info("test")






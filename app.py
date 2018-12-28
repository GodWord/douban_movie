# -*- coding:utf-8 -*-
import io
import sys

from selenium import webdriver

from jobs.douban_short import run
from utils.logger import Logger

if __name__ == '__main__':
    Logger()
    run()

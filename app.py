# -*- coding:utf-8 -*-
from selenium import webdriver

from jobs.douban_short import run, get_browser
from utils.logger import Logger

browser = webdriver.Chrome()
if __name__ == '__main__':
    Logger()
    browser = get_browser()
    run()
    browser.quit()

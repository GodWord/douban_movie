# -*- coding:utf-8 -*-

from jobs.douban_short import run
from jobs.word_count import word_count
from utils.logger import Logger

if __name__ == '__main__':
    Logger()
    run()
    word_count

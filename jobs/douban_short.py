# -*- coding:utf-8 -*-
import json
import logging
import multiprocessing
import os
import random
import string

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pymysql import InternalError
from selenium import webdriver

from setting.setting import API_SHORT, MOVIE_CONFIG, SHORT_CONFIG, HEADER, API_URL, FILE_PATH, \
    FILE_NAME, PROCESSES_NUM, DB_CONNS, TABLE_CONFIG

FLAG = True

logger = logging.getLogger('short')


def get_headers(str_headers):
    def __id_generator(size=11, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    user_agents = [
        'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Avant Browser)',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SE 2.X MetaSr 1.0; SE 2.X MetaSr 1.0; .NET CLR 2.0.50727; SE 2.X MetaSr 1.0)',
        'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; The World)',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
        'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.8.131 Version/11.11',
        'Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; en) Presto/2.8.131 Version/11.11',
    ]

    headers = dict(map(lambda x: x.strip(' ').split(':', 1), str_headers.strip().split('\n')))

    headers['User-Agent'] = user_agents[random.randint(0, len(user_agents) - 1)]
    headers['Cookie'] = 'bid=' + __id_generator() + headers['Cookie'][15:]
    return headers


def get_json(url, headers=None, params=None, **kwargs):
    req = requests.get(url, headers=headers, params=params, **kwargs)
    req.encoding = req.apparent_encoding
    try:
        data = json.loads(req.content)
    except Exception as e:
        print(e)
        data = dict()
    return data


def get_movie():
    for num in range(MOVIE_CONFIG['page_start'], MOVIE_CONFIG['page_total'], MOVIE_CONFIG['page_limit']):
        headers = get_headers(HEADER)
        data = get_json(API_URL.format(MOVIE_CONFIG['page_limit'], num), headers=headers)
        for movie in data['subjects']:
            movie['movie_id'] = movie.pop('id')
            yield movie


# def save_csv(movie):
#     file.write(movie['title'] + ',')
#     file.write(movie['rate'] + ',')
#     file.write(movie['url'] + ',')
#     file.write(movie['cover'] + ',')
#     for short in movie['messages']:
#         message = str(short).strip().replace(',', '，').replace('\r', '').replace('\n', '')
#         print(message)
#         print("------------------------------------------------------")
#         file.write(message + ',')
#     file.write('\n')


def get_browser():
    chromedriver = "C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe"
    os.environ["webdriver.chrome.driver"] = chromedriver
    option = webdriver.ChromeOptions()
    # option.add_argument('headless')
    # browser = webdriver.Chrome(chromedriver, chrome_options=option)
    browser = webdriver.Chrome(chromedriver)
    return browser


def get_tag(text, selector):
    bs = BeautifulSoup(text, 'lxml')
    res = bs.select(selector)
    return res


def del_other(ll):
    new_list = [list(t) for t in set(tuple(_) for _ in ll)]
    new_list.sort(key=ll.index)
    return new_list


def get_sql_by_list(table_name, columns, values):
    """
    根据values生成sql插入语句
    :param table_name:
    :param columns:
    :param values:
    :return:
    """
    if len(columns) != len(values):
        return None, None
    sql = 'insert into {}(%s) values(%s);'.format(table_name)

    sql = sql % ('{}' * len(columns), '%s' * len(columns))
    sql = sql.replace(r'}{', '},{').replace(r's%', 's,%')
    sql = sql.format(*columns)

    return sql, values


def table_exists(table_name, conn):
    """
    判断表是否存在
    :param table_name:
    :param conn:
    :return:
    """
    import re
    cur = conn.cursor()
    sql = "show tables;"
    cur.execute(sql)
    tables = [cur.fetchall()]
    table_list = re.findall('(\'.*?\')', str(tables))
    table_list = [re.sub("'", '', each) for each in table_list]

    if table_name in table_list:
        return True  # 存在返回True
    else:
        return False  # 不存在返回False


def execute_sql(conn, sql, values=None):
    cur = conn.cursor()
    logger.info('正在执行sql:[%s]' % (sql,))
    cur.execute(sql)
    res = cur.fetchall()
    cur.close()
    return res


def to_db(df):
    conn = DB_CONNS['default']()
    sql_list = list(map(lambda x: get_sql_by_list('douban_short', list(x.keys()), list(x.values())), df))
    # 若表不存在，则创建表，0为占位符(无意义,三目运算符所需)
    try:
        list(map(lambda x: execute_sql(conn, TABLE_CONFIG[x]) if not table_exists(x, conn) else 0, TABLE_CONFIG.keys()))
    except Exception as e:
        logger.error(e)
    # 执行sql,保存数据
    logger.info('正在保存数据:%s' % (sql_list,))
    cur = conn.cursor()
    for sql, value in sql_list:
        try:
            cur.execute(sql, value)
            conn.commit()
        except InternalError as e:
            logger.error(e)
    cur.close()
    conn.close()


def deal_by_process(movie, start):
    from app import browser
    browser.get(API_SHORT % (movie['movie_id'], start))  # 需要打开的网址
    html = browser.page_source
    short_tags = get_tag(html, 'div.comment span.short')
    # rate_tags = get_tag(html, 'div.ratings-on-weight span.rating_per')
    res = []
    # alone_rates = []
    for short in short_tags:
        # for rate_tag in rate_tags:
        #     alone_rates.append(rate_tag.text)
        # all_rates.append(alone_rates)
        movie['message'] = short.text.strip().replace('\r', '').replace('\n', '')
        res.append(movie.copy())
    to_db(res)


def run():
    movies = get_movie()
    pool = multiprocessing.Pool(processes=PROCESSES_NUM)
    for movie in movies:
        for start in range(SHORT_CONFIG['start'], SHORT_CONFIG['short_num'], 20):
            print(start)
            deal_by_process(movie, start)
            # pool.apply_async(deal_by_process, (browser, movie, start))

    pool.close()
    pool.join()

    print("============================================")
    print('爬取完成')
    print("============================================")
    # path = r'H:\PycharmProjects\douban_movie'
    # os.system("explorer.exe %s" % path)
    # os.startfile(r'.\result.csv')

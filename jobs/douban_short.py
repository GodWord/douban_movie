# -*- coding:utf-8 -*-
import hashlib
import json
import logging
import multiprocessing
import os
import random
import string

import requests
from bs4 import BeautifulSoup
from pymysql import InternalError
from selenium import webdriver

from setting.setting import API_SHORT, MOVIE_CONFIG, SHORT_CONFIG, HEADER, API_URL, PROCESSES_NUM, DB_CONNS, \
    TABLE_CONFIG

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


def execute_sql(conn, sql):
    cur = conn.cursor()
    print('正在执行sql:[%s]' % (sql,))
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
        print(e)
    # 执行sql,保存数据
    print('正在保存数据:%s' % (sql_list,))
    cur = conn.cursor()
    for sql, value in sql_list:
        try:
            cur.execute(sql, value)
            conn.commit()
        except InternalError as e:
            print(e)
    cur.close()
    conn.close()


def get_html(url):
    print('正在获取网页:%s' % (url,))
    chromedriver = "C:\Program Files (x86)\Google\Chrome\Application\chromedriver.exe"
    os.environ["webdriver.chrome.driver"] = chromedriver
    option = webdriver.ChromeOptions()
    option.add_argument('headless')
    browser = webdriver.Chrome(chromedriver, chrome_options=option)
    # browser = webdriver.Chrome(chromedriver)
    browser.get(url)  # 需要打开的网址
    html = browser.page_source
    browser.quit()
    return html


def get_md5_value(value):
    # 将字符串转成md5
    md5 = hashlib.md5()  # 获取一个MD5的加密算法对象
    md5.update(value.encode("utf8"))  # 得到MD5消息摘要
    md5_vlaue = md5.hexdigest()  # 以16进制返回消息摘要，32位
    return md5_vlaue


def deal_by_process(movie, start):
    url = API_SHORT % (movie['movie_id'], start)
    html = get_html(url.strip())
    short_tags = get_tag(html, 'div.comment span.short')
    comment_info_tags = get_tag(html, 'span.comment-info a')
    votes_tags = get_tag(html, 'span.votes')
    comment_time_tags = get_tag(html, 'span.comment-time')
    res = []
    for (short, user, votes, comment_time) in zip(short_tags, comment_info_tags, votes_tags, comment_time_tags):
        movie['message'] = short.text.strip().replace('\r', '').replace('\n', '')
        movie['username'] = user.text.strip().replace('\r', '').replace('\n', '')
        movie['votes'] = votes.text.strip().replace('\r', '').replace('\n', '')
        movie['comment_time'] = comment_time.attrs['title'].strip().replace('\r', '').replace('\n', '')
        movie['message_username_md5'] = get_md5_value(movie['message'] + movie['username'])
        res.append(movie.copy())
    if len(res) == 0:
        return
    to_db(res)


def run():
    movies = get_movie()
    pool = multiprocessing.Pool(processes=PROCESSES_NUM)
    for movie in movies:
        for start in range(SHORT_CONFIG['start'], SHORT_CONFIG['short_num'], 20):
            # deal_by_process(movie, start)
            pool.apply_async(deal_by_process, (movie, start))

    pool.close()
    pool.join()

    print("============================================")
    print('爬取完成')
    print("============================================")
    # path = r'H:\PycharmProjects\douban_movie'
    # os.system("explorer.exe %s" % path)
    # os.startfile(r'.\result.csv')

# -*- coding:utf-8 -*-
import os

import pymysql

douban_short_create_sql = """
CREATE TABLE `douban_short` (
  `id`  INT primary key NOT NULL auto_increment  COMMENT '主键ID',
  `username` varchar(100) DEFAULT NULL COMMENT '用户名',
  `movie_id` BIGINT NULL COMMENT '电影ID',
  `votes` INT default 0 COMMENT '觉得有用',
  `rate` FLOAT(6,2) DEFAULT 0 NULL COMMENT '评分',
  `cover_x` INT NULL COMMENT '海报宽度',
  `cover_y` INT NULL COMMENT '海报长度',
  `is_new` BOOLEAN DEFAULT FALSE NULL COMMENT '是否为新电影',
  `playable` BOOLEAN DEFAULT FALSE NULL COMMENT '是否能播放',
  `title` varchar(30) DEFAULT NULL COMMENT '电影名称',
  `url` varchar(800) DEFAULT NULL COMMENT '电影URL',
  `cover` varchar(800) DEFAULT NULL COMMENT '海报URL',
  `message_username_md5` varchar(32) UNIQUE not null COMMENT '用户名和评论的MD5',
  `message` TEXT DEFAULT NULL COMMENT '短评',
  `comment_time`  datetime NULL DEFAULT CURRENT_TIMESTAMP COMMENT '评论时间',
  `update_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='豆瓣短评表';
"""
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TABLE_CONFIG = {
    'douban_short': douban_short_create_sql,
}

API_HOME = 'http://movie.douban.com/j/search_subjects'
API_URL = 'http://movie.douban.com/j/search_subjects?type=movie&tag=%E6%9C%80%E6%96%B0&sort=recommend&page_limit={}&page_start={}'
FILE_PATH = '.'  # 结果文件路径
FILE_NAME = 'result.csv'  # 结果文件名称
MOVIE_CONFIG = {
    'page_limit': 20,  # 每次请求电影条数(建议不要设置过小，过小容易封ip)
    'page_start': 0,  # 电影从第几条开始获取
    # 爬取电影类型,共有[‘热门','最新','经典','可播放','豆瓣高分','冷门佳片','华语','欧美','韩国','日本','动作','喜剧','爱情','科幻','悬疑','恐怖','动画‘ ]
    'tag': '最新',
    'page_total': 40,  # 爬取电影数量
}
SHORT_CONFIG = {
    'start': 0,  # 短评从第几条开始获取
    'short_num': 20  # 爬取短评条数
}
DB_CONNS = {
    'default': lambda: pymysql.connect(host="localhost", port=3306, user="root",
                                       password="training", db="crawler_db", charset='utf8mb4'),
}
PROCESSES_NUM = 2
API_SHORT = """
https://movie.douban.com/subject/%s/comments?start=%d&limit=20&sort=new_score&status=P&percent_type=
"""

HEADER = """
Accept:text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
Accept-Language:zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7
Cache-Control:no-cache
Connection:keep-alive
Cookie:bid=_YiWD7Jayk0; douban-fav-remind=1; ll="108309"; _vwo_uuid_v2=D52D6B197AA63FDA49463045DEBB06C69|1030a8d0d2199dd0991d94e1155ca1e2; __yadk_uid=BhfX9dykHmfyTLt8DSbmaNJrUsRx1LSM; gr_user_id=52719b10-0c5a-470e-843c-7650c88cf1f5; viewed="5977150_30304849_3995526"; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1544183032%2C%22https%3A%2F%2Fwww.google.com.sg%2F%22%5D; _pk_ses.100001.4cf6=*; __utma=30149280.598247501.1528771024.1544013668.1544183032.11; __utmb=30149280.0.10.1544183032; __utmc=30149280; __utmz=30149280.1544183032.11.8.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utma=223695111.1595282729.1534683203.1544013668.1544183032.4; __utmb=223695111.0.10.1544183032; __utmc=223695111; __utmz=223695111.1544183032.4.2.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); _pk_id.100001.4cf6=a3a9da58c92d9e62.1534683203.4.1544183041.1544015609.; ap_v=0,6.0
Host:movie.douban.com
Pragma:no-cache
Referer:https://movie.douban.com/explore
Upgrade-Insecure-Requests:1
User-Agent:Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
"""

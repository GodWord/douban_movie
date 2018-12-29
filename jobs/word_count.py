# -*- coding:utf-8 -*-
import logging
import os
import random
from functools import reduce

import jieba
import matplotlib.pyplot as plt
import pandas as pd
from wordcloud import WordCloud

from setting.setting import DB_CONNS, BASE_DIR
from utils.logger import Logger

logger = logging.getLogger('word_count')


def get_message_by_db(sql):
    conn = DB_CONNS['default']()
    res = pd.read_sql(sql, conn)
    return res


def save_img(movie_id, wordcloud):
    path = os.path.join(BASE_DIR, 'static\\img\\')
    logger.info('movie_id:%d' % (movie_id,))
    logger.info('wordcloud:%s' % (wordcloud,))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.savefig(os.path.join(path, str(movie_id) + '.png'))


if __name__ == '__main__':
    Logger()
    sql = 'SELECT `message`, movie_id FROM douban_short'
    logger.info('开始查询数据库')
    df = get_message_by_db(sql)
    logger.info('开始短评聚合')
    res = df.groupby(by=['movie_id'])['message'].sum().reset_index()  # type:pd.DataFrame
    logger.info('开始短评分词')
    res['cut_text'] = res['message'].apply(lambda x: " ".join(jieba.cut(x)))
    logger.info('开始词频统计')
    res['wordcloud'] = res['cut_text'].apply(lambda x: WordCloud(font_path="C:/Windows/Fonts/simfang.ttf",
                                                                 background_color="white", width=1000,
                                                                 height=880).generate(x))
    logger.info('开始绘制词云')
    res.apply(lambda x: save_img(x['movie_id'], x['wordcloud']), axis=1)

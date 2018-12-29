# -*- coding:utf-8 -*-
import pandas as pd

__author__ = 'zhoujifeng'
__date__ = '2018/12/29 10:05'
from setting.setting import DB_CONNS

from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        conn = DB_CONNS['default']()
        sql = 'select movie_id,title,cover from douban_short group by movie_id'
        df = pd.read_sql(sql, conn)
        df['img'] = '/static/img/' + df['movie_id'].astype('str') + '.png'
        df.drop(['movie_id'], axis=1, inplace=True)
        res = df.values
    return render_template('index.html', data=res)


if __name__ == '__main__':
    app.run()

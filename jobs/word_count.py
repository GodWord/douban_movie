# -*- coding:utf-8 -*-
from functools import reduce

import jieba
import matplotlib.pyplot as plt
from wordcloud import WordCloud


def get_generator_by_csv(file_path: str, encoding='gb18030'):
    with open(file_path, 'r', encoding=encoding) as file:
        data = file.readlines()
    for values in data:
        yield values.split(',')[-1]


if __name__ == '__main__':
    data = get_generator_by_csv('./result.csv')
    commentFreDic = dict()
    txt = reduce(lambda x, y: x + ',' + y, data)
    cut_text = " ".join(jieba.cut(txt))
    wordcloud = WordCloud(font_path="C:/Windows/Fonts/simfang.ttf", background_color="white", width=1000,
                          height=880).generate(cut_text)
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    plt.savefig('wordcloud.png')

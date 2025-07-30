"""
股票黑名单：

json文件
{
  "host": "192.168.0.113",
  "user": "*",
  "password": "*",
  "database": "*",
  "port": 3306
}

# 创建表
sql = '''
create table if not exists stock_blacklist(
id int primary key auto_increment,
symbol varchar(6) not null comment '股票代码不能为空',
name varchar(32) not null comment '股票名称不能为空',
reason text not null comment '原因不能为空',
notes text
)charset=utf8;
'''

黑名单原因格式：
【财务造假】具体事件

"""
import json
import re

import pandas as pd
import pymysql

from cnquant.config.config_data_path import get_file_path_db_conn
from cnquant.core.name_symbol import name2symbol, symbol2name


class BlackList(object):
    def __init__(self):
        self.conn_data = self._open_conn_data()
        self.db = pymysql.connect(**self.conn_data)
        self.cursor = self.db.cursor()  # 使用 cursor() 方法创建一个游标对象 cursor

    @staticmethod
    def _open_conn_data():
        with open(get_file_path_db_conn(), 'r') as f:
            data = json.load(f)
        return data

    def insert_blacklist(self):
        # 输入股票名称或代码
        while True:
            try:
                symbol = input('请输入需要添加的黑名单股票代码或名称：')
                if not re.compile(r'^\d+$').match(symbol):
                    symbol = name2symbol(symbol)
                break
            except ValueError:
                print('股票名称或代码输入有误，请重新输入：')

        # 添加数据
        # 先查询一下表里面的symbol，
        sql = 'SELECT * FROM stock_blacklist WHERE symbol = %s'
        self.cursor.execute(sql, symbol)
        result = self.cursor.fetchall()

        name = symbol2name(symbol)

        if result:  # 如果已经存在黑名单内，把原因添加一下
            original_reason = result[0][3]
            print(f'{name}已经在黑名单里面，原因是：{original_reason}')
            reason = input('请补充黑名单原因：')
            modified_reason = original_reason + '\n' + reason

            update_sql = 'UPDATE stock_blacklist SET reason = %s WHERE symbol = %s'
            self.cursor.execute(update_sql, (modified_reason, symbol))
            self.db.commit()
            print(f'{name}黑名单原因已经添加！')

        else:  # 如果不在黑名单，添加到新的行里面
            print(f'{name}不在黑名单内')
            reason = input('请输入加入黑名单原因：')

            sql_insert = "INSERT INTO stock_blacklist (symbol, name, reason) VALUES (%s, %s, %s)"
            self.cursor.execute(sql_insert, (symbol, name, reason))
            self.db.commit()
            print(f'{name}已经添加到黑名单！')

    def query_blacklist(self, symbol):
        sql = 'SELECT * FROM stock_blacklist WHERE symbol = %s'
        self.cursor.execute(sql, symbol)
        result = self.cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in self.cursor.description])
        return df

    def query_blacklist_all(self):
        sql = 'SELECT * FROM stock_blacklist'
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        df = pd.DataFrame(result, columns=[i[0] for i in self.cursor.description])
        return df

    def get_blacklist_symbols(self):
        """
        查询所有的黑名单股票代码
        """
        sql = 'SELECT symbol FROM stock_blacklist'
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        blacklist_symbols = [i[0] for i in result]
        return blacklist_symbols

    def __del__(self):
        # 关闭数据库连接
        self.db.close()


if __name__ == '__main__':
    blacklist = BlackList()

    # while True:
    #     blacklist.insert_blacklist()

    df = blacklist.query_blacklist_all()
    # df = blacklist.query_blacklist(symbol='000001')
    print(df)

    s = blacklist.get_blacklist_symbols()
    print(s)
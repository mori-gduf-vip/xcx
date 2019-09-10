# -*- coding: utf-8 -*-
import pymysql
import confighelper

# db模块抽出来 代码整洁 传路径 读配置
def get_connection():
    db_config= confighelper.load_yml('common', 'db_config.yml').get('dbconfig')
    print db_config
    return pymysql.connect(host=db_config.get('host'),
                           user=db_config.get('user'),
                           password=db_config.get('password'),
                           db=db_config.get('db'),
                           charset=db_config.get('charset'),
                           cursorclass=pymysql.cursors.DictCursor)


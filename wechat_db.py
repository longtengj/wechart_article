# coding=utf8
import time

import pymysql
import json

# 连接数据库
tablename = 'article'
db = pymysql.connect(host='127.0.0.1', user='root', passwd='root', db='mydb', charset='utf8mb4')
cur = db.cursor()
cur.execute('USE mydb')



# 保存数据
def sava_article(mp_name,title, img,source,html_json,update_time):
    try:
        cur.execute(
            'INSERT INTO ' + tablename + ' (mp_name,title, img,source,html_json,update_time) VALUES (%s, %s,%s, %s,%s,%s)',
            (mp_name.strip().replace("\n", ""), title.strip().replace("\n", ""),img.strip().replace("\n", ""), source.strip().replace("\n", ""),
             html_json.strip().replace("\n", ""),time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(update_time))))
        cur.connection.commit()
        print(title[0])
        print("------------------------  插入成功  ----------------------------------")
    except:
        print(title[0])
        print("------------------------  插入失败  ----------------------------------")


# 连接数据库
def get_connect():
    try:
        # 创建表
        cur.execute(
            'CREATE TABLE ' + tablename + ' (id BIGINT(7) NOT NULL AUTO_INCREMENT,mp_name VARCHAR(300), title VARCHAR(1000), img VARCHAR(4500), source VARCHAR(4500), html_json VARCHAR(3000), update_time VARCHAR(100),created TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(id))')
    except pymysql.err.InternalError as e:
        print(e)
    # 修改表字段
    cur.execute('ALTER DATABASE mydb CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci')
    cur.execute(
        'ALTER TABLE ' + tablename + ' CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')


# cur.execute(
#     'ALTER TABLE ' + tablename + ' CHANGE title title VARCHAR(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
# cur.execute(
#     'ALTER TABLE ' + tablename + ' CHANGE img img VARCHAR(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
# cur.execute(
#     'ALTER TABLE ' + tablename + ' CHANGE source source VARCHAR(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
# cur.execute(
#     'ALTER TABLE ' + tablename + ' CHANGE time time VARCHAR(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')


if __name__ == '__main__':
    get_connect()
    sava_article("qwq", "124324", "wrer", "wrewt", "wrer", 1586511589);
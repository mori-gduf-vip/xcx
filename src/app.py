# -*- coding: utf-8 -*-
import hashlib
import json
import os
import urllib
import certifi
import urllib3
import urllib3.contrib.pyopenssl
from qiniu import Auth
from qiniu import BucketManager
from util import confighelper, logutil, dbutil, codeutil

# db模块抽出来 代码整洁
connection = dbutil.get_connection();
request = urllib3.PoolManager(cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())

# 七牛云模块
# 需要填写你的 Access Key 和 Secret Key
access_key = '_KrWKd4NSoWzCY5IjcVJ68XdIytPXuSe5xGO-Fqg'
secret_key = '_kTYdEpGp5N5IjdEiOOFv7NgZHHwxzqQxHY6ee67'
# 构建鉴权对象
q = Auth(access_key, secret_key)
bucket = BucketManager(q)
bucket_name='qltxxcx'

class WxCatch:
    url_request = ""
    header_define = {}
    business_type = ""
    proxies = {}

    def init_header_and_url(self, url, business_type):
        self.business_type = business_type
        self.url_request = url
        yaml_data = confighelper.load_yml(self.business_type, 'catch_config.yml')
        self.header_define = yaml_data.get('header')
        ip_port = yaml_data.get('catchconfig').get('ipproxy').get('url')  # 从api中提取出来的代理IP:PORT
        username = yaml_data.get('catchconfig').get('ipproxy').get('username')
        password = yaml_data.get('catchconfig').get('ipproxy').get('password')
        basic_pwd = codeutil.base_code(username, password)
        self.proxies = 'http://{}'.format(ip_port)
        self.header_define['Proxy-Authorization'] = 'Basic %s' % (basic_pwd)
        logutil.print_msg("yaml获取并设置头与url", "")

    # call init_header_and_url   post
    def post_api(self, post_data):

        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
            'Accept': "application/json",
            'TK': self.tk
        }

        proxy = urllib3.ProxyManager('http://127.0.0.1:8888', headers=headers)
        response = proxy.request_encode_body('POST', self.url_request, fields=post_data, encode_multipart=False)

        print(response.data);
        return response.data

    # input  type  Choosing Business  method
    def analyse_business(self, page, type):
        logutil.print_msg("业务操作", str(page) + "--" + str(type))
        # 业务处理  遍历类别  从1开始
        post_data = {
            "type": type,
            "order": 1,
            "page": page,
            "page_size": 20,
            "is_auth": 0
        }
        # 字典排序  str加密  作为tk
        sorted_data = sorted(post_data.items(), key=lambda x: x[0], reverse=False)
        before_tk = '';
        for key in sorted_data:
            before_tk += key[0] + "=" + str(key[1]) + "&"
        before_tk = before_tk[0:before_tk.rindex("&")]
        tk = hashlib.md5(hashlib.sha256(before_tk).hexdigest()).hexdigest()
        print tk
        self.tk = tk
        # sha256加密

        resp = json.loads(self.post_api(post_data))
        if resp['code'] == 1:
            resplist = resp['data']['list']
            addlist = []
            for l in resplist:
                img1 = l['img_arr1']
                img2 = l['img_arr2']
                print img1
                print img2
                addlist.append(img1)
                addlist.append(img2)
            self.persist_mysql(addlist, page, type)

        else:
            print "抓取失败"
        logutil.print_msg("分析返回数据并进行业务操作入库", "")

    def persist_mysql(self, list, page, type):
        cursor = connection.cursor();
        # 入库
        for l in list:
            print l['id']
            # 插入新的数据
            try:
                sql = "INSERT INTO `qltx` (`id`,`img_id`,`imgurl`,`type`,`page`) VALUES (%s,%s,%s,%s,%s)"
                cursor.execute(sql, (l['id'], l['img_id'], l['imgurl'], type, page))
                connection.commit()
                logutil.print_msg("持久化入库", "成功")
            except:
                logutil.print_msg("持久化入库", "异常")
                connection.rollback()

                continue


def catch():
    wxCatch = WxCatch()
    wxCatch.init_header_and_url('https://ntx.qqtn.com/api/couple/coupleImgList', 'qltx')
    for t in range(0, 20):
        for i in range(1, 40):
            try:
                wxCatch.analyse_business(i, t)
            except:
                break
    # wxCatch.analyse_business(2, 20)

    connection.close();


def upload_from_db():
    # 查询数据库
    sql = "select * from qltx where copy_done = 0"
    cursor = connection.cursor();
    cursor.execute(sql)
    resultlist = cursor.fetchall()
    i = 0
    # 遍历操作 更新路径和操作标示
    for r in resultlist:
        download_and_update(r, cursor)
        i = i + 1
        print i
    logutil.print_msg("处理", "处理七牛云")


def download_and_update(po, cursor):
    url = po['imgurl']
    suffix_url = url.replace('https://', '/')
    img_path = confighelper.get_img_path();
    img_path = img_path + suffix_url
    img_prefix = img_path[0:img_path.rindex("/")]
    print suffix_url
    print url
    key = suffix_url
    ret, info = bucket.fetch(url, bucket_name, key)
    print(info)
    assert ret['key'] == key
    if os.path.exists(img_path):
        print("File have already exist. skip")
    else:
        try:
            if not os.path.exists(img_prefix):
                os.makedirs(img_prefix)
            print img_path
            print url
            urllib.urlretrieve(url, img_path)
            print po['is_keep']
            print po['attr1']
        except Exception as e:
            print("Error occurred when downloading file, error message:")
            print e


def main():
    upload_from_db()

if __name__ == "__main__":
    main()

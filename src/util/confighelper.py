# -*- coding: utf-8 -*-
import os

import yaml

import logutil


def load_yml(filepath, filename):
    resource_path = ('%s%s%s%s%s' % (os.path.abspath('..'), os.sep, 'resource', os.sep, filepath))
    logutil.print_msg('资源文件', resource_path)
    with open(resource_path + os.sep + filename, 'r') as f:
        yaml_data = yaml.load(f, Loader=yaml.FullLoader)
    print(yaml_data)
    # 根据路径解析header
    return yaml_data

def get_img_path():
    cur_path = ('%s%s%s%s%s' % (os.path.abspath('..'), os.sep, 'resource', os.sep, 'img'))
    return cur_path

# -*- coding: utf-8 -*-

""" DESCRIPTION OF WORK"""
__author__ = ["draymonders"]

import argparse
import logging
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import math
import requests
import lxml
import re
import time
import datetime
import traceback
import random
import os
from dotenv import load_dotenv


logging.basicConfig(
    level=logging.DEBUG,
    format='[%(filename)s:%(lineno)s - %(funcName)s %(asctime)s;%(levelname)s] %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S'
)
log = logging.getLogger(__file__)

def get_header(city_name):
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.146 Safari/537.36',
        'Referer': 'https://%s.lianjia.com/ershoufang/' % city_name
    }

def get_cookie_dict(cookies=''):
    if not cookies:
        load_dotenv()
        cookies = os.getenv('COOKIES')
        log.info(f"find env [cookies]")
    cookie_dict = {}
    # cookies = 'select_city=130400; lianjia_ssid=df0d52e3-8043-4586-a1ef-98904ad66681; lianjia_uuid=f05fc479-d360-41a1-83c9-7f1823d5d4df; Hm_lvt_46bf127ac9b856df503ec2dbf942b67e=1746676661; HMACCOUNT=3BF74A5346930089; sajssdk_2015_cross_new_user=1; sensorsdata2015jssdkcross=%7B%22distinct_id%22%3A%22196ae0abc80cc1-02ee390e78d0b2-1a525636-1484784-196ae0abc814133%22%2C%22%24device_id%22%3A%22196ae0abc80cc1-02ee390e78d0b2-1a525636-1484784-196ae0abc814133%22%2C%22props%22%3A%7B%22%24latest_traffic_source_type%22%3A%22%E8%87%AA%E7%84%B6%E6%90%9C%E7%B4%A2%E6%B5%81%E9%87%8F%22%2C%22%24latest_referrer%22%3A%22https%3A%2F%2Fwww.google.com%2F%22%2C%22%24latest_referrer_host%22%3A%22www.google.com%22%2C%22%24latest_search_keyword%22%3A%22%E6%9C%AA%E5%8F%96%E5%88%B0%E5%80%BC%22%7D%7D; _jzqa=1.2181010913316240400.1746676661.1746676661.1746676661.1; _jzqc=1; _jzqx=1.1746676661.1746676661.1.jzqsr=google%2Ecom|jzqct=/.-; _jzqckmp=1; _ga=GA1.2.664893915.1746676673; _gid=GA1.2.199881847.1746676673; login_ucid=2000000175383146; lianjia_token=2.0015b66f0c72a1208a041b463de49c08cc; lianjia_token_secure=2.0015b66f0c72a1208a041b463de49c08cc; security_ticket=DzXyN2DnbxaDsLxF43odM2kR2rk7KX5cfXtghPlbUto7uH0NYZlgANZZpi92wxsiTjQFEG4njOIgZ5u1l32DoQOQCs0XOYFF+uOEJS+S3wr12v2p9Hqr0Z/3SZeWE+ueRemAzzpF0eB41xpON7yWmuuufUOR/cODv6On6IXJ8ZY=; ftkrc_=be0b6923-8589-431b-81d0-9e420c5fb08f; lfrc_=e25feeaf-4ec4-4132-957f-a79596df4c8a; Hm_lvt_efa595b768cc9dc7d7f9823368e795f1=1746676794; Hm_lpvt_efa595b768cc9dc7d7f9823368e795f1=1746676810; Hm_lpvt_46bf127ac9b856df503ec2dbf942b67e=1746678061; _jzqb=1.8.10.1746676661.1'
    for cookie in cookies.split(';'):
        name, value = cookie.split('=', 1)
        cookie_dict[name] = value
    return cookie_dict

def get_session():
    sess = requests.session()
    cookie_dict = get_cookie_dict()
    for name, value in cookie_dict.items():
        sess.cookies.set(name, value)
    return sess

def re_match(re_pattern, string, errif='-'):
    try:
        return re.findall(re_pattern, string)[0].strip()
    except IndexError:
        return errif

class HouseFinder:
    def __init__(self, city_name, district_dict, debug=False):
        self.city_name = city_name # 城市名称, eg: "hd"
        self.district_dict = district_dict # {'丛台区': 'congtaiqu'}
        self.debug = debug
        self.sess = get_session()
        self.headers = get_header(city_name)

    def get_house_info(self, district_cn, district_en):
        """
        获取房屋总数
        """
        house_num_url = ('https://%s.lianjia.com/ershoufang/{}/' % self.city_name).format(district_en)
        html = self.sess.get(house_num_url, headers=self.headers, allow_redirects=True, timeout=3).text
        house_num = re.findall('共找到<span> (.*?) </span>套.*二手房', html)[0].strip()
        return house_num

    def get_info_dic(self, info, district_cn):
        """
        解析Html文本，获取房屋信息
        Args:
            info: 房屋信息Html
            district_cn: 区县名称, eg: "丛台区"
            city_name: 城市名称, eg: "hd"
        Returns:
            info_dic: 房屋信息
        """  
        house_id = re.findall('data-housecode="(.*?)"', str(info))[0]
        title = re_match('target="_blank">(.*?)</a><!--', str(info))
        title = title.strip().replace(',', '-').replace('，', '-').replace(' ', '-')

        info_dic = {
            "house_id": house_id, # 房屋id
            'title': title, # 标题
            'district': district_cn, # 区县
            'community': re_match('xiaoqu.*?target="_blank">(.*?)</a>', str(info)), # 小区
            'position': re_match('<a href.*?target="_blank">(.*?)</a>.*?class="address">', str(info)), # 位置
            'tax': re_match('class="taxfree">(.*?)</span>', str(info)),
            'total_price': float(re_match('class="totalPrice totalPrice2"><i> </i><span class="">(.*?)</span><i>万', str(info))),
            'unit_price': float(re_match('data-price="(.*?)"', str(info))),
            'link': f'https://{self.city_name}.lianjia.com/ershoufang/{house_id}.html',
        }
        icons = re.findall('class="houseIcon"></span>(.*?)</div>', str(info))[0].strip().split('|')
        info_dic.update({
            'hourse_type': icons[0].strip(), # 户型
            'hourse_size': float(icons[1].replace('平米', '')), # 面积 单位平米
            'direction': icons[2].strip(), # 朝向
            'fitment': icons[3].strip(), # 装修
            'level': icons[4].strip(), # 层高
            'build_type': icons[5].strip(), # 建筑类型 板楼
        })
        return info_dic

    def get_house_list_by_page(self, district_cn, district_en, page_id):
        url = f'https://{self.city_name}.lianjia.com/ershoufang/{district_en}/pg{page_id+1}/'
        html = self.sess.get(url, headers=self.headers, allow_redirects=True, timeout=5).text
        soup = BeautifulSoup(html, 'lxml')
        house_html_list = soup.find_all(class_="info clear")
        return house_html_list

    def crawl_data(self):
        """
        爬虫抓取数据
        """
        total_num = 0
        err_num = 0
        house_list = []

        for district_cn, district_en in self.district_dict.items():
            # district_cn = "丛台区", district_en = "congtaiqu"
            
            house_num = self.get_house_info(district_cn, district_en)
            log.info('{}: 二手房源共计「{}」套'.format(district_cn, house_num))
            time.sleep(random.randint(2, 10))
            
            # 最多能抓3000页，每页30个
            total_page = int(math.ceil(min(3000, int(house_num)) / 30.0))
            for i in tqdm(range(total_page), desc=district_cn):
                house_html_list = self.get_house_list_by_page(district_cn, district_en, i)
                for house_html in house_html_list:
                    try:
                        house_dict = self.get_info_dic(house_html, district_cn)
                        house_list.append(house_dict)
                    except Exception as e:
                        traceback.print_exc()
                        log.info("icons <= 5 means not house, but car position")
                        err_num += 1
                    total_num += 1
                if self.debug: # 调试模式下，只抓一页
                    break
                time.sleep(random.randint(1, 5))
        log.info("after crawl, total_num[%s] err_num[%s]" % (total_num, err_num))
        return house_list

def get_city_area_dict(city_name):
    """
    获取城市区域
    """
    area_dic = {}
    area_dic_small = {}
    if city_name == "bj":
        # all beijing
        area_dic = {'朝阳区': 'chaoyang',
                    '海淀区': 'haidian',
                    '西城区': 'xicheng'
        }
        area_dic_small = {
            '五道口': 'wudaokou',
        }
    elif city_name == "hz":
        area_dic = {
            '钱塘区': 'qiantangqu'
                    }
        area_dic_small = {
            # define as real need
        }
    elif city_name == "hd":
        area_dic = {
            '丛台区': 'congtaiqu',
            '复兴区': 'fuxingqu',
            '邯山区': 'hanshanqu',
            '经开区': 'jingkaiqu'
        }
        area_dic_small = {
            # define as real need
            '丛台区': 'congtaiqu',
        }
    else:
        print("no area dic defined in city:%s, fill it first" % city_name)
        exit(1)
    return area_dic, area_dic_small

def main():

    example_word = """
        DESCRIBE ARGUMENT USAGE HERE
        python house_finder.py --help
    """

    parser = argparse.ArgumentParser(prog=__file__, description='code description', epilog=example_word,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    # add parameter if needed
    parser.add_argument('-v', '--version', help='version of code', action='version', version='%(prog)s 1.0')
    parser.add_argument('--area_name', help='area to fetch', type=str, default='all')
    parser.add_argument('--city_name', help='city to fetch', type=str, default='bj')
    parser.add_argument('--debug', help='debug mode', type=int, default=0)
    args = parser.parse_args()

    city_name = args.city_name

    area_dic, area_dic_small = get_city_area_dict(city_name)
    
    sess = get_session()
    headers = get_header(city_name)
    sess.get('https://%s.lianjia.com/ershoufang/' % city_name, headers=headers)

    district_dict = area_dic
    if args.area_name == 'small':
        district_dict = area_dic_small
    log.info(f"开始抓取 城市[{city_name}] 区县 {list(district_dict.keys())}")

    house_finder = HouseFinder(city_name, district_dict, debug=args.debug)
    house_list = house_finder.crawl_data()
    house_df = pd.DataFrame(house_list)
    os.makedirs(f"data/{city_name}", exist_ok=True)
    os.chdir(f"data/{city_name}")
    house_df.to_csv("dt_%s.csv" % (datetime.datetime.now().strftime('%Y%m%d')), encoding='utf-8-sig')


if __name__ == '__main__':
    main()

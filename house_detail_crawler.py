# -*- coding: utf-8 -*-
# 获取房源详情信息

import argparse
import base64
import logging
import os
import pandas as pd
import requests
import time
from bs4 import BeautifulSoup
from io import BytesIO
from tqdm import tqdm
import random
from house_finder import get_header, get_session

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(filename)s:%(lineno)s - %(funcName)s %(asctime)s;%(levelname)s] %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S'
)
log = logging.getLogger(__file__)

def get_image_base64_from_url(url: str):
    """
    从URL获取图片并转换为base64格式
    Args:
        url: 图片URL地址
    Returns:
        str: base64编码的图片数据
    """
    # todo @yubing base64 格式提取
    try:
        response = requests.get(url)
        response.raise_for_status()
        image_data = BytesIO(response.content)
        base64_data = base64.b64encode(image_data.getvalue()).decode('utf-8')
        img_type = ''
        if base64_data.startswith('/9j/'):
            img_type = 'jpeg'
        elif base64_data.startswith('iVBORw0KGgo'):
            img_type = 'png'
        elif base64_data.startswith('R0lGODlh'):
            img_type = 'gif'
        elif base64_data.startswith('Qk2'):
            img_type = 'bmp'
        elif base64_data.startswith('SUkq'):
            img_type = 'tiff'
        return f"data:image/{img_type};base64,{base64_data}"
    except Exception as e:
        log.error(f"获取图片失败: {url}, 错误: {e}")
        return ""

class HouseImages:
    def __init__(self, url_dict={}):
        # url_dict: {url: desc}
        self.url_dict = url_dict
        # urls: [url] 房屋图
        self.urls = list(url_dict.keys())
    
    def img_datas(self, is_hx=False):
        img_urls = self.get_urls(is_hx=is_hx)

        base64_datas = []
        final_urls = []
        
        for url in img_urls:
            if url == '':
                continue
            base64_data = get_image_base64_from_url(url)
            if base64_data == '':
                continue
            base64_datas.append(base64_data)
            final_urls.append(url)
        return final_urls, base64_datas 
    
    def messages(self):
        # 喂给大模型的输入
        msgs = []
        msgs.append({
            "type": "text",
            "text": "以下是户型图"
        })
        
        urls, base64_datas = self.img_datas(is_hx=True)
        for base64_data in base64_datas:
            msgs.append({
                    "type": "image_url",
                    "image_url": {
                        "url": base64_data
                    }
                })
        urls, base64_datas = self.img_datas(is_hx=False)
        msgs.append({
            "type": "text",
            "text": "以下是各个房间的图"
        })
        for base64_data in base64_datas:
            msgs.append({
                "type": "image_url",
                "image_url": {
                    "url": base64_data
                }
            })
        return msgs

    def to_dict(self):
        return {
            "urls": ";".join(self.urls),
            "url_dict": ";".join([f"{k}##{v}" for k, v in self.url_dict.items()])
        }

    def get_urls(self, is_hx=False, max_num=8):
        img_urls = []
        for url, _type in self.url_dict.items():
            is_real_hx = (_type == "户型图")
            if is_hx:
                if is_real_hx:
                    img_urls.append(url)
            else:
                if is_real_hx:
                    continue
                img_urls.append(url)
        return img_urls[:max_num]

    def __str__(self):
        hx_urls = self.get_urls(is_hx=True)
        urls = self.get_urls(is_hx=False)
        return f"户型图: {hx_urls[:1]}; 房屋图片: {urls[:1]}"

def format_img_size(url, origin="120x80", dest="450x300"):
    return url.replace(origin, dest)

class HouseDetailCrawler:
    def __init__(self, house_id, url):
        self.house_id = house_id
        self.url = url
        self.sess = get_session()
        self.headers = get_header()
        
    def extract_house_img(self):
        # 从url获取图片
        html_text = self.sess.get(self.url, headers=self.headers, allow_redirects=True, timeout=3).text
        hx_urls = [] # 户型图
        url_dict = {} # 房屋图片
        pic_container = None
        try:
            soup = BeautifulSoup(html_text, 'lxml')
            pic_container = soup.find_all('ul', class_="smallpic")[0]
        except Exception as e:
            print(f"[extract_house_img] html_text {html_text} 解析失败: {e}")
            return None
        if not pic_container:
            log.info("[get_house_images] 未找到图片容器")
            return None
        try:
            li_tags = pic_container.find_all('li')
            for li in li_tags:
                # 在每个 li 标签下找到 img 标签
                img_desc = li['data-desc'] if li.has_attr('data-desc') else ''
                img_tag = li.find('img')
                if img_tag and img_tag.has_attr('src'):
                    # 获取 src 属性值，并去除可能存在的前后空格和反引号
                    img_url = img_tag['src'].strip().strip('`')
                    img_url = format_img_size(img_url)
                    # if img_desc == '户型图':
                    #     hx_urls.append(img_url)
                    # else:
                    url_dict[img_url] = img_desc
        except Exception as e:
            print(f"[extract_house_img] pic_container {html_text[:100]} 解析失败: {e}")
            return None
        house_images = HouseImages(url_dict=url_dict)
        return house_images

def get_house_details(house_df, debug_num=0):
    success_num, fail_num = 0, 0
    house_details = []
    log.info(f"房源信息 共 {len(house_df)} 条")
    idx = 0
    for _, row in tqdm(house_df.iterrows(), total=len(house_df)):
        if debug_num > 0 and idx >= debug_num:
            break
        idx += 1
        house_id = int(row['house_id'])
        url = row['link']
        crawler = HouseDetailCrawler(house_id, url)
        try:
            house_imgs = crawler.extract_house_img()
            if house_imgs:
                house_detail = {
                    "house_id": house_id,
                    "link": url
                }
                house_detail.update(house_imgs.to_dict())
                house_details.append(house_detail)
        except Exception as e:
            if debug_num:
                log.error(f"house_id {house_id} 获取房源详情失败:, 错误: {e}")
            fail_num += 1
            continue
        success_num += 1
        time.sleep(random.randint(2, 5))
    log.info(f"房源详情获取成功: {success_num}, 失败: {fail_num}")
    return house_details

def main():
    parser = argparse.ArgumentParser(description='House Image Crawler')
    parser.add_argument('--house_csv', type=str, default='', help='house finder csv file')
    parser.add_argument('--debug_num', help='debug num', type=int, default=0)

    args = parser.parse_args()

    # 原始房源
    house_df = pd.read_csv(args.house_csv) 
    log.info(f"房源信息路径: {args.house_csv} 共 {len(house_df)} 条")
    
    dest_csv_path = args.house_csv.replace('.csv', '_details.csv')
    if os.path.exists(dest_csv_path):
        dest_df = pd.read_csv(dest_csv_path)
        house_df = house_df[~house_df['house_id'].isin(dest_df['house_id'])]
        log.info(f"已存在房源详情: {len(dest_df)} 条, 剩余 {len(house_df)} 条")

    house_details = get_house_details(house_df, args.debug_num)
    
    log.info(f"房源详情获取成功: {len(house_details)}")
    # 合并dest_df 和 detail_df
    detail_df = pd.DataFrame(house_details)
    if os.path.exists(dest_csv_path):
        dest_df = pd.read_csv(dest_csv_path)
        detail_df = pd.concat([dest_df, detail_df], ignore_index=True)
        log.info(f"合并后房源详情: {len(detail_df)} 条")
    detail_df.to_csv(dest_csv_path, index=False)


if __name__ == '__main__':
    main()
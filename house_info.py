# -*- coding: utf-8 -*-
import pandas as pd

from house_detail_crawler import HouseImages

class HouseInfo:
    def __init__(self, house_id, df_path="./data/hd/dt_20250508_cut_final.csv"):
        self.house_id = int(house_id)
        self.house_df = self.load_house_base_info(df_path)
        # print(len(self.house_df))
    
    def load_house_base_info(self, df_path):
        """
        加载房源基础信息
        """
        df = pd.read_csv(df_path)
        df["house_id"] = df["house_id"].astype(int)
        return df[df.house_id == self.house_id]

    def get_base_info(self):
        house_header_dict = {
            "title": "标题",
            "district": "区县",
            "community": "小区",
            "position": "位置",
            "total_price": "总价",
            "unit_price": "单价",
            "house_type": "户型",
            "hourse_size": "面积",
            "direction": "朝向",
            "fitment": "装修",
            "level": "楼层",
            "build_type": "建筑类型"
        }

        house_strs = []
        house_df = self.house_df
        for i, row in house_df[house_df['house_id'] == self.house_id].iterrows():
            # print(item)
            item = row.to_dict()
            for en, cn in house_header_dict.items():
                val = item.get(en, '-')
                if en == 'total_price':
                    val = f'{val}万'
                if en == 'unit_price':
                    val = f'{val}元/平'
                house_strs.append(f"{cn}: {val}")
            break
        base_info = "，".join(house_strs)
        return base_info
    
    def get_house_images(self):
        house_imgs = None
        url_dict = {}
        for _, row in self.house_df.iterrows():
            item = row.to_dict()
            url_dict_str = item.get("url_dict", "")
            if url_dict_str == "":
                continue
            urls = url_dict_str.split(";")
            for url in urls:
                url, desc = url.split("##")
                url_dict[url] = desc
            if len(url_dict) > 0:
                house_imgs = HouseImages(url_dict=url_dict)
                break
        return house_imgs
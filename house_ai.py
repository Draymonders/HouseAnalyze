# -*- coding: utf-8 -*-

import pandas as pd
import argparse
import logging
from house_info import HouseInfo
from dotenv import load_dotenv
from volcenginesdkarkruntime import Ark
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

class HouseAI:
    def __init__(self, house_id, user_input, api_key="", model=""):
        self.house_id = int(house_id)
        self.house_info = HouseInfo(house_id)
        if user_input:
            user_input = user_input.strip()
        self.user_input = user_input
        load_dotenv()
        if not api_key  and not model:
            
            api_key = os.getenv("LLM_API_KEY")
            # 选第一个模型
            model = os.getenv("LLM_MODELS").split(";")[0].split("##")[1]
        self.api_key = api_key
        self.model = model
        self.llm_cli = Ark(api_key=self.api_key, base_url=os.getenv("LLM_API_URL"))

    def gen_prompt(self):
        msgs = []
        
        msgs.append({
            "role": "system",
            "content": [{
                "type": "text",
                "text": "# 目标"
                +"\n你是一个房产专家，根据房屋信息和用户需求，给出满意分（最高100分）简明阐述对应打分依据"
                +"\n - 如果不满足用户预期，分值不超过50分"
                +"\n# 示例"
                +"\n-满意分: 85分。根据用户需求来看，户型图南北通透、依据房屋图房间装修干净简洁、总价在用户预期内"
                +"\n-满意分: 30分。根据用户需求来看，户型不够方正、房子建设时间较久、房子装修较差"
            }]
        })
        contents = []
        if self.user_input:
            contents.append({
                "type": "text",
                "text": f"# 用户需求\n{self.user_input}"
                # "text": f"{self.user_input}"
            })
        if self.house_info:
            contents.append({
                "type": "text",
                "text": f"# 房源信息\n{self.house_info.get_base_info()}"
            })
            house_imgs = self.house_info.get_house_images()
            if house_imgs:
                contents.extend(house_imgs.messages())
        msgs.append({
            "role": "user",
            "content": contents
        })
        return msgs
    
    def messages(self, prompt=None):
        if not prompt:
            prompt = self.gen_prompt()
        content = ""
        try:
            resp = self.llm_cli.chat.completions.create(
                model=self.model,
                messages=prompt
            )
            content = resp.choices[0].message.content
        except Exception as e:
            log.error(f"调用AI失败: {e}")
        return content

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--house_id', type=int, help='an integer for the accumulator')
    parser.add_argument('--user_input', type=str, help='an integer for the accumulator')

    args = parser.parse_args()
    house_ai = HouseAI(args.house_id, args.user_input)
    print(house_ai.messages())
# -*- coding: utf-8 -*-
# 大模型代替客户识别房间信息

## python gradio_demo.py 
import os
import gradio as gr
from collections import OrderedDict
from house_info import HouseInfo
from dotenv import load_dotenv
from house_detail_crawler import get_image_base64_from_url
from house_ai import HouseAI
import tempfile
import base64

load_dotenv()

def get_model_api_key():    
    api_key = os.getenv("LLM_API_KEY")
    return api_key

def get_model():
    models = os.getenv("LLM_MODELS")
    model_confs = OrderedDict()
    for model_str in models.split(";"):
        model_strs = model_str.strip().split("##")
        if len(model_strs) != 2:
            continue
        model_name = model_strs[0].strip()
        model = model_strs[1].strip()
        model_confs[model_name] = {"name": model_name, "model": model}
    return model_confs

def get_temp_file(url):
    url = url.replace("450x300", "210x140")
    base64_data = get_image_base64_from_url(url)
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        temp_file.write(base64.b64decode(base64_data.split(",")[1]))
        temp_file_path = temp_file.name
        return temp_file_path
    return ""

def query_house_info(house_id):
    house = HouseInfo(house_id)
    base_info = house.get_base_info()
    # print("房屋基础信息", base_info)

    house_imgs = house.get_house_images()
    hx_urls = house_imgs.get_urls(is_hx=True)
    urls = house_imgs.get_urls(is_hx=False)
    
    hx_urls = [get_temp_file(hx_url) for hx_url in hx_urls]
    urls = [get_temp_file(url) for url in urls]
    return base_info, hx_urls, urls

async def ai_judge_house(house_id, model_select="", prompt=""):
    # print("=== hit here ===")
    api_key = get_model_api_key()
    model = get_model()[model_select]["model"]
    ai = HouseAI(house_id, prompt, model=model, api_key=api_key)
    return ai.messages()

async def agent_screen_intention(object_id, model_select="", scene="fake", prompt=""):
    api_key, model = "", ""
    if model_select in model_confs:
        api_key = model_confs[model_select]["ak"]
        model = model_confs[model_select]["model"]
    print(f"object_id: {object_id}, scene: {scene}")
    ag = RoomAgent(object_id, ak=api_key, img_model=model)
    llm_out = ""
    if scene=="fake":
        llm_out = ag.fake_screen_intention()    
    else:
        llm_out = ag.common_screen_intention(prompt)
    return llm_out

# 创建 Gradio 界面
with gr.Blocks() as ai_house_identity:
    gr.Markdown("# AI优选好房")
    with gr.Row():
        model_confs = get_model()
        model_keys = list(model_confs.keys())
        with gr.Column(scale=1):
            model_select = gr.Dropdown(choices=model_keys, label="模型选择", value=model_keys[0])
        with gr.Column(scale=1):
            id_input = gr.Textbox(label="请输入房屋ID")
        with gr.Column(scale=3):
            prompt = gr.Textbox(label="用户需求", visible=True, interactive=True)
        with gr.Column(scale=1):
            submit_btn = gr.Button("查询")
    with gr.Row():
        with gr.Column(scale=2):
            hx_urls = gr.Gallery(label="户型图", columns=1)    
        with gr.Column(scale=4):
            urls = gr.Gallery(label="房屋图片", columns=4)
    with gr.Row():
        with gr.Column(scale=1):
            base_info = gr.Textbox(label="房屋基础信息")
        with gr.Column(scale=1):
            llm_out = gr.Textbox(label="AI输出")
    submit_btn.click(
        fn=query_house_info,
        inputs=[id_input],
        outputs=[base_info, hx_urls, urls]
    ).then(
        fn=ai_judge_house,
        inputs=[id_input, model_select, prompt],
        outputs=llm_out
    )

# root_path 是 merlin 自动生成的路径，需要点击访问链接，得到跳转后的路径获得
ai_house_identity.launch(server_name="[::]", server_port=8008, share=True, root_path="/house_ai")
# House-Analyze

房屋分析、找到意向的房子

## 处理流程

1. 批量获取房屋基础数据
2. 获取装修图、户型图
3. 结合基础数据和相关图，以及用户需求，让AI给出满意分（0-100），并给出相关判定原因
4. 筛选符合条件的小区及其相关户型，对应的房子

文件结构

```
|-- house_finder.py: 抓取房源简要信息
|-- house_cut.ipynb: 房源信息裁剪，包括层高、单价、总价
|-- house_detail_crawler.py: 抓取房源详情信息（户型图、房屋图）
|-- house_detail_merge.py: 合并房源信息
|-- house_info.py: 房屋信息结构化处理
|-- house_ai_page.py: 房屋AI优选网页调试
|-- house_ai.py: 房屋AI优选 (待增加批量处理数据)
```

## 使用方法

- 安装依赖

```
conda create -n house_analyze python=3.10
pip install -r requirements.txt
```

- 登录 bj.lianjia.com，获取cookie字段，填入.env_template文件，执行如下命令

```
cp .env_template .env
```

- 执行城市数据抓取

```
python house_finder.py --city_name hd --area_name small --debug 1
```

相关字段介绍

```
title: 标题
district: 区县
community: 小区
position: 位置
total_price: 总价
unit_price: 单价
house_type: 户型
hourse_size: 面积
direction: 朝向
fitment: 装修
level: 楼层
build_type: 建筑类型
```

# 参考

本项目参考了如下项目，在此表示感谢

- [lianjia-eroom-analysis](https://github.com/linpingta/lianjia-eroom-analysis)

# 免责声明

本项目永远作为一个免费项目使用，仅用于学习交流使用，使用者不得用于谋利或访问非公开数据。

请尊重相关房产网站的使用规则，本程序只可用于适度访问公开数据，严禁修改本程序访过于频繁地进行访问，严禁修改本程序访问任何非公开数据。

数据只能用于个人使用，不支持数据共享，不能用于任何商业用途，请遵守中国相关法律
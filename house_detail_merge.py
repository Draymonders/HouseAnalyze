# -*- coding: utf-8 -*-

import pandas as pd
import argparse
import logging

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='House Image Crawler')
    parser.add_argument('--house_csv', type=str, default='', help='house finder csv file')
    args = parser.parse_args()

    origin_csv = args.house_csv
    detail_csv = origin_csv.replace(".csv", "_details.csv")
    final_csv = origin_csv.replace(".csv", "_final.csv")
    
    origin_df = pd.read_csv(origin_csv)
    dest_df = pd.read_csv(detail_csv)


    log.info(f"原始数量 {len(origin_df)} 详情数量 {len(dest_df)}")

    dest_df = pd.merge(origin_df, dest_df[["house_id", "url_dict"]], on="house_id", how="inner")
    log.info(f"合并后数量 {len(dest_df)} 写入 {final_csv}")
    dest_df.to_csv(final_csv, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()
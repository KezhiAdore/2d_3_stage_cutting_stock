import os
import pandas as pd
from settings import cache_dir
from utils import dill_load, dill_save

def presolve_csv(path, data_prefix=None):
    
    cache_path=os.path.join(cache_dir,f"{data_prefix}_order.pkl")
    if not cache_path is None and os.path.exists(cache_path):
        return dill_load(cache_path)
    
    # 读取csv
    df_B = pd.read_csv(path)
    df_B1_order = df_B.groupby(['item_order'])
    item_material_type = df_B['item_material'].unique()

    order_area_list = [0 for _ in range(len(df_B1_order.groups))]
    order_num_list = [0 for _ in range(len(df_B1_order.groups))]
    order_material_list = [[0 for _ in range(len(item_material_type))] for _ in range(len(df_B1_order.groups))]

    # dataset 由area num material——list组成
    dataset = pd.DataFrame(columns=['order_index', 'area', 'num', 'material_list'])
    for order, group in df_B1_order:
        order_index = int(order[5:])

        total_area = 0
        total_item_num = 0
        total_metrial_num = [0 for _ in range(len(item_material_type))]
        for index, row in group.iterrows():
            total_area += row['item_length']*row['item_width']
            total_item_num += row['item_num']
            for j in range(len(item_material_type)):
                if row['item_material'] == item_material_type[j]:
                    total_metrial_num[j] += row['item_num']
                
        order_area_list[order_index-1] = total_area
        order_num_list[order_index-1] = total_item_num
        order_material_list[order_index-1] = total_metrial_num
        # 在dataset中append添加一行
        dataset = dataset.append({'order_index':order_index, 'area':total_area, 'num':total_item_num, 'material_list':total_metrial_num}, ignore_index=True)
    
    order_info={
        "order_area_list": order_area_list,
        "order_num_list": order_num_list,
        "order_material_list": order_material_list,
    }
    dill_save(order_info, cache_path)
    return order_info
    
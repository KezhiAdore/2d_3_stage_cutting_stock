import os
import pandas as pd
from settings import cache_dir
from utils import dill_load, dill_save
import numpy as np


def batch_generate(order_info, data_prefix, batch_count = 54, use_cache = True):
    
    cache_path=os.path.join(cache_dir,f"{data_prefix}_batch.pkl")
    if os.path.exists(cache_path) and use_cache:
        return dill_load(cache_path)
    
    MAX_AREA = 250000000
    MAX_NUM = 1000
    order_material_list = order_info["order_material_list"]
    order_area_list = order_info["order_area_list"]
    order_num_list = order_info["order_num_list"]

    order_material_variaty = [sum(order_material_list[i])  for i in range(len(order_material_list))]
    #patterns是一个二维数组，第一维度是batch索引，第二维度是order索引
    order_material_list = np.array(order_material_list)
    # order_material_list = order_material_list / order_material_list.max(axis=1, keepdims=True)
    # 建立dataframe关联id，area，num，material，variaty
    df = pd.DataFrame(columns=['order_index', 'area', 'num', 'material_list', 'variaty'])
    df['order_index'] = range(len(order_area_list))
    df['area'] = order_area_list
    df['num'] = order_num_list
    df['material_list'] = order_material_list.tolist()
    df['variaty'] = order_material_variaty

    # 按照variaty数对order进行排序
    df = df.sort_values(by='variaty', ascending=False)

    # 再将order依次排入material最匹配的batch中

    def calc_list_correlation(list1, list2):
        # list之间sum(min(list1[i], list2[i]))/sum(list1+list2)
        list1 = np.array(list1)
        list2 = np.array(list2)
        # 归一化
        # list1 = list1 /np.max(list1)
        # list2 = list2 /np.max(list2)

        list3 = np.minimum(list1, list2)
        list4 = np.maximum(list1, list2)
        divided = np.sum(list4)

        
        return np.sum(list3)/divided

    
    # 讲pattern初始化为varity最大的order，
    batch = pd.DataFrame(columns=['batch_index', 'order_list', 'area_sum', 'num_sum', 'patterns'])
    batch.loc[0] = [0,[0+1], df.iloc[0]['area'], df.iloc[0]['num'], df.iloc[0]['material_list']]
    init_material_list = [df.iloc[0]['material_list']]#第一维度是batch索引，第二维度是material索引
    for i in range(batch_count):
        # batch.loc[i] = [i,[i], df, 0, df.iloc[i]['material_list']]
        # 找到跟前面相似度最低的order进行初始化
        correlation_list = [[] for i in range(len(init_material_list))]

        correlation_list = [[calc_list_correlation(init_material_list[j],df.iloc[jj]['material_list']) for jj in range(len(df))] for j in range(len(init_material_list))]
        # print(correlation_list)
        max_correlation = np.array(correlation_list).max(axis=0)#[np.max(correlation_list[jj]) for jj in range(batch_count)] # 剩下一个维度是init过的batch
        #index_max_corrlation = [np.argmax(correlation_list[j]) for j in range(len(init_material_list))]# 剩下一个维度是init过的batch
        index_max = np.argmin(max_correlation)
        # print(max_correlation)
        # min_correlation第一维度是init_material_list，第二维度是order
        # print(correlation_list)
        print(index_max)
        batch.loc[i] = [i,[index_max+1], df.iloc[index_max]['area'], df.iloc[index_max]['num'], df.iloc[index_max]['material_list']]
        
        init_material_list.append(df.iloc[index_max]['material_list'])
        # print('init_material_list', init_material_list)

    test_corr = []
    for i in range(len(df)):
        # 计算当前order与每个batch的相关性
        # 去重
        if i+1 in np.concatenate(batch['order_list'].values):
            continue
        order_material = df.iloc[i]['material_list']
        # 找到相关性list
        correlation_list = [ calc_list_correlation(order_material, batch.iloc[j]['patterns']) for j in range(batch_count)]

        for j in range(batch_count):
            #找到最大的相关性
            max_index = np.argmax(correlation_list)        
            
            # 如果当前batch的area和num都小于最大值，那么就将当前order加入到该batch中
            if batch.iloc[max_index]['area_sum'] + df.iloc[i]['area'] < MAX_AREA and batch.iloc[max_index]['num_sum'] + df.iloc[i]['num'] < MAX_NUM:
                batch.loc[max_index]['order_list'].append(i+1)#df.iloc[i]['order_index']
                batch['area_sum'][max_index] += df.iloc[i]['area']
                batch['num_sum'][max_index] += df.iloc[i]['num']
                batch['patterns'][max_index] = [batch.loc[max_index]['patterns'][k] and df.iloc[i]['material_list'][k] for k in range(len(df.iloc[i]['material_list']))]
                test_corr.append(correlation_list[max_index])
                break
            correlation_list[max_index] = -1
        if j>=batch_count-1:
            print('得增加batch数量')
            raise ValueError(f'batch count {batch_count} is too small 得增加batch数量')
        print(batch)

    #统计batch中的order的总数
    order_count = 0
    order_list = []
    for i in range(batch_count):
        order_count += len(batch.iloc[i]['order_list'])
        order_list += batch.iloc[i]['order_list']
    order_list.sort()
    print('order_count', order_count)
    print('order_list', order_list)

    patterns = [[0 for _ in range(len(df))] for _ in range(batch_count)]
    for i in range(len(batch)):
        for j in batch.iloc[i]['order_list']:
            patterns[i][j-1] = 1

    solution = dict(zip([i for i in range(batch_count)], [1 for i in range(batch_count)]))
    
    batch_info={
        "patterns": patterns,
        "solution": solution
    }
    dill_save(batch_info, cache_path)
    return batch_info
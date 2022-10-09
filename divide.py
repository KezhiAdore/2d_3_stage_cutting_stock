import pandas as pd
from settings import division_dir
import os

def divided_csv(path,batch_info,data_prefix):
    
    patterns = batch_info["patterns"]
    solution = batch_info["solution"]
    
    df_B = pd.read_csv(path)
    df_B_order = df_B.groupby(['item_order'])
    dataframe_batch_list = []
    for key, value in solution.items():
        # print(patterns[key])
        # print(value)
        data_frame_batch = pd.DataFrame(columns=['item_id', 'item_material', 'item_num', 'item_length', 'item_width', 'item_order'])
        for i in range(len(df_B_order)):
            if patterns[key][i] != 0:
                data_frame_batch = data_frame_batch.append(df_B_order.get_group('order'+str(i+1)), ignore_index=True)
        dataframe_batch_list.append(data_frame_batch)
        # print(data_frame_batch)
    #     print("-----------------------")
    # print(dataframe_batch_list[3])
    # print('finish')
    
    # clear division cache
    data_division_dir=os.path.join(division_dir,data_prefix)
    os.system(f"rm -rf {data_division_dir}")
        
    for i in range(len(dataframe_batch_list)):
        # 按照item_material拆分dataframe
        item_material_type = dataframe_batch_list[i]['item_material'].unique()
        for j in range(len(item_material_type)):
            # 如果不存在文件夹则新建
            dir_path=os.path.join(division_dir,data_prefix,str(i))
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            file_path=os.path.join(dir_path,item_material_type[j]+'.csv')
            dataframe_batch_list[i][dataframe_batch_list[i]['item_material'] == item_material_type[j]].to_csv(file_path)


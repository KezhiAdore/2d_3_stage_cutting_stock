import pandas as pd
import os
from concurrent.futures import ProcessPoolExecutor
import datetime

import settings
from pattern_generator import PatternGenerator
from settings import dataA_paths,dataB_paths,P1_ans_dir,P2_ans_dir,pattern_figures_dir,division_dir,cache_dir
from utils import json_load,json_save
from packing import presolve_csv
from greedy_batch import batch_generate
from divide import divided_csv

SOLVE_A=False
SOLVE_B=True

for name, value in settings.__dict__.items():
    if "dir" in name:
        dir_path = value
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
def solve_batch(args)->PatternGenerator:
    batch_num,material,filepath,batch_figure_dir,L,W=args
    df=pd.read_csv(filepath)
    pg=PatternGenerator(df,L,W,multi_process=False)
    pg.generate_patterns()
    pg.export_patterns()
    # pg.export_pattern_figure(batch_figure_dir)
    print(f"solved batch {filepath}")
    return pg
            
def solve_A(args):
    # unpacking args
    data_path,ans_path,figure_dir,result_path,L,W=args
    
    df=pd.read_csv(data_path)
    pg=PatternGenerator(df,L,W)
    pg.generate_patterns()
    pg.export_patterns(ans_path)
    pg.export_pattern_figure(figure_dir)
    
    result = {
        "total_plate_number": pg._plate_number,
        "total_plate_area": pg._plate_number*pg._L*pg._W,
        "total_require_area": pg.total_require_area,
        "total_use_ratio": pg.use_ratio,
    }
    
    json_save(result,result_path)
    return result

def solve_B(args):
    data_path,ans_path,figure_dir,result_path,L,W,batch_size=args
    # get data name
    data_prefix=data_path[data_path.rfind("/")+1:].replace(".csv","")
    
    order_info=presolve_csv(data_path,data_prefix)
    try:
        batch_info=batch_generate(order_info,data_prefix,batch_size,use_cache=False)
        divided_csv(data_path,batch_info,data_prefix+f"_{batch_size}")
    except:
        return None
    
    divided_csv_dir=os.path.join(division_dir,data_prefix+f"_{batch_size}")
    batch_num_list=os.listdir(divided_csv_dir)
    
    msgs=[]
    for batch_num in batch_num_list:
        batch_dir=os.path.join(divided_csv_dir,batch_num)
        material_list=[filename[:filename.find(".csv")] for filename in os.listdir(batch_dir)]
        for material in material_list:
            filepath=os.path.join(batch_dir,f"{material}.csv")
            batch_figure_dir=os.path.join(figure_dir,batch_num,material)
            msgs.append((batch_num,material,filepath,batch_figure_dir,L,W))
    
    # multiprocessing computing
    with ProcessPoolExecutor(9) as pool:
        results=pool.map(solve_batch,msgs,chunksize=20)
        
    # sort results
    pg_dict={}
    for i,pg in enumerate(results):
        batch_num=int(msgs[i][0])
        material=msgs[i][1]
        if batch_num not in pg_dict.keys():
            pg_dict[batch_num]={}
        pg_dict[batch_num][material]=pg
    
    result={}
    # export answer
    plate_id=0
    last_batch_plate_id=0
    total_require_area=0
    ans_df=pd.DataFrame()
    for batch_num in pg_dict.keys():
        batch_require_area=0
        for pg in pg_dict[batch_num].values():
            total_require_area+=pg.total_require_area
            batch_require_area+=pg.total_require_area
            
            temp_df=pg.export_patterns()
            temp_df["原片序号"]+=plate_id
            temp_df["批次序号"]=batch_num
            ans_df=ans_df.append(temp_df,ignore_index=True)
            
            plate_id+=pg._plate_number
        
        batch_plate_num=plate_id-last_batch_plate_id
        last_batch_plate_id=plate_id
        batch_plate_area=batch_plate_num*L*W
        # result[batch_num]={
        #     "batch_plate_num": batch_plate_num,
        #     "batch_plate_area": batch_plate_area,
        #     "batch_require_area": batch_require_area,
        #     "batch_use_ratio": batch_require_area/batch_plate_area,
        # }
            
    # ans_df.to_csv(ans_path)
    
    total_plate_area=plate_id*L*W
    use_ratio=total_require_area/total_plate_area
    
    result.update({
        "data": data_prefix,
        "total_plate_num": plate_id,
        "total_plate_area": total_plate_area,
        "total_require_area": total_require_area,
        "total_use_ratio": use_ratio,
    })
    result_path=result_path[:result_path.rfind(".json")]+"_"+str(batch_size)+".json"
    json_save(result,result_path)
    return result

if __name__=="__main__":
    L=2440
    W=1220
    
    if SOLVE_A:
        # solve problem A
        start_time=datetime.datetime.now()
        msgs=[(
            dataA_paths[i],
            os.path.join(P1_ans_dir,f"A{i+1}.csv"),
            os.path.join(pattern_figures_dir,f"A{i+1}"),
            os.path.join(P1_ans_dir,f"A{i+1}.json"),
            L,W,) for i in range(4)]
        
        with ProcessPoolExecutor(4) as pool:
            results = pool.map(solve_A,msgs)
            
        for i, result in enumerate(results):
            print(f"The result of dataset A{i+1} is following: ")
            print(result)
        
        end_time=datetime.datetime.now()
        time_cost=end_time-start_time
        print("time cost:",time_cost)
    
    if SOLVE_B:
        # solve problem B
        start_time=datetime.datetime.now()
        msgs=[]
        for batch_size in range(40,30,-2):
            msgs.extend([(
            dataB_paths[i],
            os.path.join(P2_ans_dir,f"B{i+1}.csv"),
            os.path.join(pattern_figures_dir,f"B{i+1}"),
            os.path.join(P2_ans_dir,f"B{i+1}.json"),
            L,W,batch_size) for i in range(5)])
        # solve_B(msgs[0])
        with ProcessPoolExecutor(25) as pool:
            results = pool.map(solve_B,msgs,chunksize=1)
        
        test_result={}
        for i,r in enumerate(results):
            batch_size=msgs[i][-1]
            if batch_size not in test_result.keys():
                test_result[batch_size]=[]
            test_result[batch_size].append(r)
        
        json_save(test_result,"test_B.json")
        
        end_time=datetime.datetime.now()
        time_cost=end_time-start_time
        print("time cost:",time_cost)
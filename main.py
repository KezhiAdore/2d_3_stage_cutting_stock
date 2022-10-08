import pandas as pd
import os
from concurrent.futures import ProcessPoolExecutor
import datetime

import settings
from pattern_generator import PatternGenerator
from settings import dataA_paths,dataB_paths,P1_ans_dir,pattern_figures_dir

for name, value in settings.__dict__.items():
    if "dir" in name:
        dir_path = value
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            
def solve_A(args):
    # unpacking args
    data_path,ans_path,figure_dir,L,W=args
    
    df=pd.read_csv(data_path)
    pg=PatternGenerator(df,L,W)
    pg.generate_patterns()
    pg.export_patterns(ans_path)
    pg.export_pattern_figure(figure_dir)
    
    result = {
        "plate_number": pg._plate_number,
        "total_plate_area": pg._plate_number*pg._L*pg._W,
        "total_require_area": pg.total_require_area,
        "use_ratio": pg.use_ratio,
    }
    return result

def solve_B(data_path,ans_path,figure_dir,L,W):
    df=pd.read_csv(data_path)
    
    result={
        "plate_num": None,
        "total_plate_area": None,
        "total_require_area": None,
        "use_ratio": None,
    }

if __name__=="__main__":
    L=2440
    W=1220
    # solve problem A
    start_time=datetime.datetime.now()
    with ProcessPoolExecutor(4) as pool:
        msgs=[(
            dataA_paths[i],
            os.path.join(P1_ans_dir,f"A{i+1}.csv"),
            os.path.join(pattern_figures_dir,f"A{i+1}"),
            L,W,
        ) for i in range(4)]
        
        results = pool.map(solve_A,msgs)
        
    for i, result in enumerate(results):
        print(f"The result of dataset A{i+1} is following: ")
        print(result)
    
    end_time=datetime.datetime.now()
    time_cost=end_time-start_time
    print("time cost:",time_cost)
    
    # solve problem B
    # with ProcessPoolExecutor(5) as pool:
    #     msgs=[]
    #     results = pool.map(solve_B,msgs)
    
    # for i,result in enumerate(results):
    #     print(f"The result of dataset B{i+1} is following: ")
    #     print(result)
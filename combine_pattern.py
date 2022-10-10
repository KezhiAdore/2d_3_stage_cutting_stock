import cv2 as cv
import os
import numpy as np
from settings import pattern_figures_dir,figures_dir

def remove_border(image):
    # image=image[730:2180,570:3370,:]  # 横版
    image=image[400:2505,1420:2515:]    # 竖版
    return image

def combine_images(image_list,row_limit,col_limit):
    image_list=[remove_border(image) for image in image_list]
    image_shape=image_list[0].shape
    blank_image=np.ones(image_shape,dtype=np.uint8)*255
    
    image_id=0
    combined_images=[]
    image_num=len(image_list)
    while image_id<image_num:
        row_image_list=[]
        for i in range(row_limit):
            col_image_list=[]
            for j in range(col_limit):
                if image_id<image_num:
                    temp_image=image_list[image_id]
                else:
                    temp_image=blank_image
                image_id+=1
                col_image_list.append(temp_image)
            row_image=np.hstack(col_image_list)
            row_image_list.append(row_image)
        combined_image=np.vstack(row_image_list)
        combined_images.append(combined_image)
    return combined_images
    

def dir_process(source_dir,dst_dir):
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    image_name_list=os.listdir(source_dir)
    image_path_list=[os.path.join(source_dir,image_name) for image_name in image_name_list]
    image_list=[cv.imread(image_path) for image_path in image_path_list]
    # combined_images=combine_images(image_list,8,3)  # 横版
    combined_images=combine_images(image_list,4,6)  # 竖版
    for index,image in enumerate(combined_images):
        image_path=os.path.join(dst_dir,f"{index}.png")
        cv.imwrite(image_path,image)

if __name__=="__main__":
    for i in range(1,5):
        source_dir=os.path.join(pattern_figures_dir,f"A{i}")
        dst_dir=os.path.join(figures_dir,"combined_patterns",f"A{i}")
        dir_process(source_dir,dst_dir)
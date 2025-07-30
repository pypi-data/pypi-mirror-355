from PepperPepper.environment import os


def collect_image_names(input_dir, output_txt, recursive=True):
    """
    收集指定路径下所有图像名称（不包含扩展名）并写入txt文件

    参数:
        input_dir (str): 输入目录路径
        output_txt (str): 输出txt文件路径
        recursive (bool): 是否递归子目录，默认True
    """
    image_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff'}

    with open(output_txt, 'w') as f:
        # 遍历方式选择 [1]()[3]()
        if recursive:
            walk_generator = os.walk(input_dir)
        else:
            walk_generator = [(input_dir, [], os.listdir(input_dir))]

        for root, dirs, files in walk_generator:
            for file in files:
                # 分离文件名和扩展名 [2]()
                filename, ext = os.path.splitext(file)
                if ext.lower() in image_exts:
                    # 构建相对路径 [3]()
                    rel_path = os.path.relpath(os.path.join(root, filename), input_dir)
                    f.write(rel_path + '\n')


if __name__ == '__main__':
    collect_image_names(input_dir='/mnt/d/code/algorithms/IRSTD/SCTransNet/datasets/IRSTD-1k/images',output_txt = '/mnt/d/code/algorithms/IRSTD/SCTransNet/datasets/IRSTD-1k/images/all_images.txt',  recursive=False)
    # print(imglist)
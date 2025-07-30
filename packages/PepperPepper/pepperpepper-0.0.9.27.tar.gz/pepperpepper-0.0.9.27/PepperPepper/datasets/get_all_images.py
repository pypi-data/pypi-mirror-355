from PepperPepper.environment import os, Image


def get_all_images(path, load_images=False):
    """
    获取指定路径下的所有图像文件路径或图像数据。

    参数:
        path (str): 要搜索的文件夹路径。
        load_images (bool): 是否加载图像数据。如果为 False，则仅返回图像文件路径。

    返回:
        list: 图像文件路径列表或加载后的图像数据列表。
    """
    # 支持的图像扩展名
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
    image_data = []

    # 遍历文件夹及其子文件夹
    for root, _, files in os.walk(path):
        for file in files:
            # 检查文件扩展名是否为图像格式
            if os.path.splitext(file)[1].lower() in image_extensions:
                file_path = os.path.join(root, file)
                if load_images:
                    try:
                        # 加载图像数据
                        img = Image.open(file_path)
                        image_data.append(img)
                    except Exception as e:
                        print(f"无法加载图像 {file_path}: {e}")
                else:
                    # 仅保存图像路径
                    image_data.append(file_path)

    return image_data


if __name__ == '__main__':
    imglist = get_all_images(path='/mnt/d/code/algorithms/IRSTD/SCTransNet/datasets/IRSTD-1k/images')
    print(imglist)

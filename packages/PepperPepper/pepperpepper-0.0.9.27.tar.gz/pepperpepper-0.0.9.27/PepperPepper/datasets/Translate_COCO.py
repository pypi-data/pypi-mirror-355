from PepperPepper.environment import os, json, Image, ET, shutil





def convert_txt_to_coco(txt_dir, image_dir, output_json, image_ext=".jpg"):
    '''
    将TXT标注文件转换为COCO格式的JSON文件

    Args:
        txt_dir (str): TXT标注文件目录（如labels/）
        image_dir (str): 图片文件目录（如images/）
        output_json (str): 输出的JSON文件路径（如dataset_coco.json）
        image_ext (str): 图片扩展名（默认为.jpg）
    '''

    coco_data = {
        'info':{},
        'licenses':[],
        'images':[],
        'annotations':[],
        'categories':[],
    }

    # 自动收集所有类别（假设类别ID从0开始）
    existing_categories = set()



    # 遍历所有TXT文件
    annotation_id = 1  # 标注ID从1开始递增
    for txt_file in os.listdir(txt_dir):
        if not txt_file.endswith(".txt"):
            continue

        # 提取图片ID（假设文件名是纯数字，如"0001.txt"对应图片"0001.jpg"）
        image_id = os.path.splitext(txt_file)[0]
        image_path = os.path.join(image_dir, f"{image_id}{image_ext}")

        # 读取图片尺寸
        try:
            with Image.open(image_path) as img:
                width, height = img.size
        except FileNotFoundError:
            print(f"警告：图片 {image_path} 不存在，跳过")
            continue



        # 添加图片信息到COCO
        coco_data['images'].append({
            'id': image_id,
            'file_name': f"{image_id}{image_ext}",
            'width': width,
            'height': height,
        })

        # 读取TXT文件并解析标注
        txt_path = os.path.join(txt_dir, txt_file)
        with open(txt_path, "r") as f:
            lines = f.readlines()


        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 解析YOLO格式：class_id x_center y_center w h
            parts = line.split()
            if len(parts) != 5:
                print(f"错误：{txt_file} 中的行格式不正确: {line}")
                continue

            # 提取数据并转换类型
            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            w = float(parts[3])
            h = float(parts[4])

            # 将归一化坐标转换为绝对坐标
            x_min = (x_center - w / 2) * width
            y_min = (y_center - h / 2) * height
            abs_w = w * width
            abs_h = h * height

            # 确保坐标不超出图像边界
            x_min = max(0, x_min)
            y_min = max(0, y_min)
            abs_w = min(width - x_min, abs_w)
            abs_h = min(height - y_min, abs_h)

            # 添加类别到categories（如果未存在）
            if class_id not in existing_categories:
                coco_data["categories"].append({
                    "id": class_id,
                    "name": str(class_id),  # 可根据实际类别名称修改
                    "supercategory": ""
                })
                existing_categories.add(class_id)





            # 添加标注信息
            coco_data["annotations"].append({
                "id": annotation_id,
                "image_id": int(image_id),
                "category_id": class_id,
                "bbox": [x_min, y_min, abs_w, abs_h],
                "area": abs_w * abs_h,
                "iscrowd": 0,
                "segmentation": []
            })

            annotation_id += 1

    # 保存为JSON文件
    with open(output_json, "w") as f:
        json.dump(coco_data, f, indent=2)
    print(f"转换完成！保存至 {output_json}")


def convert_voc_to_coco(voc_root, coco_root, splits=['train', 'val']):
    # 创建标准COCO目录
    os.makedirs(os.path.join(coco_root, 'annotations'), exist_ok=True)
    for split in splits:
        os.makedirs(os.path.join(coco_root, 'images', split), exist_ok=True)

    # 自动收集所有类别
    all_classes = set()
    for split in splits:
        with open(os.path.join(voc_root, 'ImageSets/Main', f'{split}.txt')) as f:
            for img_id in f.read().splitlines():
                xml_path = os.path.join(voc_root, 'Annotations', f'{img_id}.xml')
                if os.path.exists(xml_path):
                    tree = ET.parse(xml_path)
                    for obj in tree.findall('object'):
                        all_classes.add(obj.find('name').text.strip())

    # 生成类别映射
    classes = sorted(list(all_classes))
    cat_map = {name: i + 1 for i, name in enumerate(classes)}

    # 处理每个数据集划分
    for split in splits:
        coco_data = {
            "images": [],
            "annotations": [],
            "categories": [{"id": v, "name": k} for k, v in cat_map.items()]
        }

        with open(os.path.join(voc_root, 'ImageSets/Main', f'{split}.txt')) as f:
            img_ids = [line.strip() for line in f]

        img_id_num = 1  # 每个split从1开始计数
        ann_id_num = 1

        for img_name in img_ids:
            # 处理图片文件
            src_img = os.path.join(voc_root, 'JPEGImages', f'{img_name}.jpg')
            dst_img = os.path.join(coco_root, 'images', split, f'{img_name}.jpg')
            if os.path.exists(src_img):
                shutil.copy(src_img, dst_img)
            else:
                continue

            # 处理标注
            xml_path = os.path.join(voc_root, 'Annotations', f'{img_name}.xml')
            if not os.path.exists(xml_path):
                continue

            tree = ET.parse(xml_path)
            root = tree.getroot()

            # 添加图片信息
            size = root.find('size')
            coco_data['images'].append({
                "id": img_id_num,
                "width": int(size.find('width').text),
                "height": int(size.find('height').text),
                "file_name": f"images/{split}/{img_name}.jpg",
            })

            # 处理每个对象
            for obj in root.findall('object'):
                name = obj.find('name').text.strip()
                if name not in cat_map:
                    continue

                bbox = obj.find('bndbox')
                xmin = int(float(bbox.find('xmin').text))
                ymin = int(float(bbox.find('ymin').text))
                xmax = int(float(bbox.find('xmax').text))
                ymax = int(float(bbox.find('ymax').text))

                coco_data['annotations'].append({
                    "id": ann_id_num,
                    "image_id": img_id_num,
                    "category_id": cat_map[name],
                    "bbox": [xmin, ymin, xmax - xmin, ymax - ymin],
                    "area": (xmax - xmin) * (ymax - ymin),
                    "iscrowd": 0
                })
                ann_id_num += 1

            img_id_num += 1

        # 保存标注文件
        with open(os.path.join(coco_root, 'annotations', f'instances_{split}.json'), 'w') as f:
            json.dump(coco_data, f)


# # 使用示例
# convert_voc_to_coco(
#     voc_root='VOC2007',  # 输入VOC目录
#     coco_root='COCO',  # 输出目录（自动创建）
#     splits=['train', 'val', 'test']
# )
















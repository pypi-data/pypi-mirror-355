from PepperPepper.environment import torch, nn, torchvision, Dataset, os, Image, np, transforms
from PepperPepper.datasets import get_all_images, get_img_norm_cfg




class DataSetLoader(Dataset):
    def __init__(self, dataset_dir, dataset_name, patch_size, img_norm_cfg=None, mode='train', if_readall_img = False):
        super(DataSetLoader, self).__init__()

        self.dataset_dir = dataset_dir + '/' + dataset_name
        self.dataset_name = dataset_name
        self.patch_size = patch_size
        self.mode = mode
        self.if_readall_img = if_readall_img

        # 读取训练样本列表
        if mode == 'train':
            with open(os.path.join(self.dataset_dir, 'img_idx', f'train_{dataset_name}.txt'), 'r') as f:
                self.train_list = f.read().splitlines()
        else:
            with open(os.path.join(self.dataset_dir, 'img_idx', f'test_{dataset_name}.txt'), 'r') as f:
                self.train_list = f.read().splitlines()

        # 图像归一化配置
        if img_norm_cfg is None:
            self.img_norm_cfg = self.get_img_norm_cfg(dataset_name, dataset_dir)
        else:
            self.img_norm_cfg = img_norm_cfg

        self.transform = self.augmentation(patch_size, mode)

        if if_readall_img:
            self.imgs_list, self.masks_list = self.all_read_img()
        else:
            self.imgs_list, self.masks_list = None, None



    def augmentation(self, patch_size=256, mode='train'):
        """
        定义数据增强操作。

        返回:
            transform (callable): 数据增强操作。
        """
        if mode == 'train':
            transform = transforms.Compose([
                # transforms.RandomCrop(size=(patch_size, patch_size), pad_if_needed=True),
                transforms.Resize(size=(patch_size, patch_size), interpolation=transforms.InterpolationMode.BILINEAR),
                transforms.RandomHorizontalFlip(p=0.5),  # 随机水平翻转
                transforms.RandomVerticalFlip(p=0.5)    # 随机垂直翻转
            ])
        else:
            transform = transforms.Compose([
                # transforms.RandomCrop(size=(patch_size, patch_size), pad_if_needed=True),
                transforms.Resize(size=(patch_size, patch_size), interpolation = transforms.InterpolationMode.NEAREST)
            ])



        return transform



    def all_read_img(self):
        imgs_list = []
        masks_list = []

        for idx, img_name in enumerate(self.train_list):
            img = Image.open((self.dataset_dir + '/images/' + self.train_list[idx] + '.png').replace('//', '/')).convert('I')
            mask = Image.open((self.dataset_dir + '/masks/' + self.train_list[idx] + '.png').replace('//', '/')).convert('I')

            # 转换为 PyTorch 张量
            img = torch.tensor(np.array(img, dtype=np.float32))  # 转换为浮点型张量
            mask = torch.tensor(np.array(mask, dtype=np.float32)) / 255.0  # 将掩码归一化到 [0, 1]
            img = self.normalize(img)

            # 如果掩码有多个通道，仅保留第一个通道
            if len(mask.shape) > 2:
                mask = mask[:, :, 0]

            # 转换为 PyTorch 张量
            # img = torch.tensor(img, dtype=torch.float32)  # 转换为 PyTorch 张量
            # mask = torch.tensor(mask, dtype=torch.float32)  # 转换为 PyTorch 张量

            # 添加通道维度
            img = img.unsqueeze(0)  # (H, W) -> (1, H, W)
            mask = mask.unsqueeze(0)  # (H, W) -> (1, H, W)

            if img.shape != mask.shape:
                print(self.train_list[idx])
                print('img shape:', img.shape)
                print('mask shape:', mask.shape)
                img = transforms.Resize((self.patch_size, self.patch_size),interpolation=transforms.InterpolationMode.BILINEAR)(img)
                mask = transforms.Resize((self.patch_size, self.patch_size), interpolation = transforms.InterpolationMode.NEAREST)(mask)
                # img = transforms.RandomCrop(size=(self.patch_size, self.patch_size), pad_if_needed=True)(img)
                # mask = transforms.RandomCrop(size=(self.patch_size, self.patch_size))(mask)

            # 数据增强
            augmented = self.transform(torch.cat([img, mask], dim=0))  # 拼接图像和掩码以同时增强
            img_patch, mask_patch = augmented[0:1], augmented[1:2]  # 分离增强后的图像和掩码

            imgs_list.append(img_patch)
            masks_list.append(mask_patch)
        return imgs_list, masks_list







    def __getitem__(self, idx):
        if self.if_readall_img:
            return self.imgs_list[idx], self.masks_list[idx]

        img = Image.open((self.dataset_dir + '/images/' + self.train_list[idx] + '.png').replace('//', '/')).convert('I')
        mask = Image.open((self.dataset_dir + '/masks/' + self.train_list[idx] + '.png').replace('//', '/')).convert('I')

        # 转换为 PyTorch 张量
        img = torch.tensor(np.array(img, dtype=np.float32))/255.0  # 转换为浮点型张量
        mask = torch.tensor(np.array(mask, dtype=np.float32)) / 255.0  # 将掩码归一化到 [0, 1]
        # img = self.normalize(img)

        # 如果掩码有多个通道，仅保留第一个通道
        if len(mask.shape) > 2:
            mask = mask[:, :, 0]

        # 转换为 PyTorch 张量
        # img = torch.tensor(img, dtype=torch.float32)  # 转换为 PyTorch 张量
        # mask = torch.tensor(mask, dtype=torch.float32)  # 转换为 PyTorch 张量

        # 添加通道维度
        img = img.unsqueeze(0)  # (H, W) -> (1, H, W)
        mask = mask.unsqueeze(0)  # (H, W) -> (1, H, W)

        if img.shape != mask.shape:
            # print(self.train_list[idx])
            # print('img shape:', img.shape)
            # print('mask shape:', mask.shape)
            img = transforms.Resize((self.patch_size, self.patch_size), interpolation=Image.BILINEAR)(img)
            mask = transforms.Resize((self.patch_size, self.patch_size), interpolation=Image.NEAREST)(mask)
            # img = transforms.RandomCrop(size=(self.patch_size, self.patch_size), pad_if_needed=True)(img)
            # mask = transforms.RandomCrop(size=(self.patch_size, self.patch_size))(mask)


        # 数据增强
        augmented = self.transform(torch.cat([img, mask], dim=0))  # 拼接图像和掩码以同时增强
        img_patch, mask_patch = augmented[0:1], augmented[1:2]  # 分离增强后的图像和掩码

        return img_patch, mask_patch

    def get_img_norm_cfg(self, dataset_name, dataset_dir):
        """获取图像归一化配置（假设是预定义的）"""
        # 这里可以根据数据集名称返回对应的均值和标准差
        # 示例：假设所有数据集使用相同的归一化配置

        if dataset_name == 'NUDT-SIRST':
            img_norm_cfg = dict(mean=float(107.80905151367188), std=float(33.02274703979492))
        elif dataset_name == 'IRSTD-1k':
            img_norm_cfg = dict(mean=float(87.4661865234375), std=float(39.71953201293945))
        elif dataset_name == 'SIRST3':
            img_norm_cfg = dict(mean=float(111.90503692626953), std=float(27.645191192626953))
        else:
            with open(dataset_dir + '/' + dataset_name + '/img_idx/train_' + dataset_name + '.txt', 'r') as f:
                train_list = f.read().splitlines()
            with open(dataset_dir + '/' + dataset_name + '/img_idx/test_' + dataset_name + '.txt', 'r') as f:
                test_list = f.read().splitlines()
            img_list = train_list + test_list
            img_dir = dataset_dir + '/' + dataset_name + '/images/'
            mean_list = []
            std_list = []
            for img_pth in img_list:
                try:
                    img = Image.open((img_dir + img_pth).replace('//', '/') + '.png').convert('I')
                except:
                    try:
                        img = Image.open((img_dir + img_pth).replace('//', '/') + '.jpg').convert('I')
                    except:
                        img = Image.open((img_dir + img_pth).replace('//', '/') + '.bmp').convert('I')
                img = np.array(img, dtype=np.float32)
                mean_list.append(img.mean())
                std_list.append(img.std())
            img_norm_cfg = dict(mean=float(np.array(mean_list).mean()), std=float(np.array(std_list).mean()))
        return img_norm_cfg




    def __len__(self):
        return len(self.train_list)


    def normalize(self, img):
        """
        对图像进行归一化。
        参数:
            img (Tensor): 输入图像。
        返回:
            img (Tensor): 归一化后的图像。
        """
        mean = torch.tensor(self.img_norm_cfg['mean'], dtype=torch.float32).view(1, 1)
        std = torch.tensor(self.img_norm_cfg['std'], dtype=torch.float32).view(1, 1)
        img = (img - mean) / std  # 按通道归一化
        return img
from PepperPepper.environment import plt, torch, np


def visualize_tensor(tensor, mean=None, std=None):
    """
    可视化PyTorch图像张量
    :param tensor: 输入张量 [1, C, H, W]
    :param mean: 预处理时使用的均值（需反归一化时提供）
    :param std: 预处理时使用的标准差（需反归一化时提供）
    """
    # 基础处理流程
    img = tensor.squeeze(0)  # 移除批次维度 → [3, 256, 256]
    img = img.permute(1, 2, 0)  # 维度转换  → [256, 256, 3]

    # 反归一化处理（如果有）
    if mean is not None and std is not None:
        img = img.detach().cpu().clone()
        for t, m, s in zip(img.permute(2, 0, 1), mean, std):  # 逐个通道处理
            t.mul_(s).add_(m)
        img = torch.clamp(img, 0, 1)  # 保证数值范围在0-1之间
    else:
        img = img.detach().cpu()

        # 转换到适合显示的格式
    np_img = img.numpy()
    if np_img.max() <= 1:  # 自动检测是否需要rescale
        np_img = np_img * 255
    np_img = np.clip(np_img, 0, 255).astype('uint8')


    return np_img

    # # 可视化
    # plt.figure(figsize=(8, 8))
    # plt.imshow(np_img)
    # plt.axis('off')
    # plt.title('Tensor  Visualization Result')
    # plt.show()


if __name__ == "__main__":
    # 测试数据生成
    dummy_data = torch.randn(1, 3, 256, 256)  # 模拟带有归一化的张量
    # dummy_data = torch.rand(1,  3, 256, 256)  # 模拟无归一化张量

    # 调用函数（根据预处理情况配置参数）
    np_img = visualize_tensor(
        dummy_data,
        mean=[0.485, 0.456, 0.406],  # ImageNet均值（如启用需反归一化）
        std=[0.229, 0.224, 0.225]  # ImageNet标准差
    )

    # 可视化
    plt.figure(figsize=(8, 8))
    plt.imshow(np_img)
    plt.axis('off')
    plt.title('Tensor  Visualization Result')
    plt.show()
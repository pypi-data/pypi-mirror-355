import os

import torch
from PIL import Image
from torchvision import transforms, models


def get_class(class_path):
    # 定义一个空字典来存储类别
    classes_dict = []
    # 打开文件
    with open(class_path, 'r', encoding='utf-8') as file:
        # 遍历文件中的每一行
        for line in file:
            # 去除每行末尾的换行符
            category = line.strip()
            # 将类别添加到字典中，值是其自身
            classes_dict.append(category)
    return classes_dict


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using {} device training.".format(device.type))
    classes_dict = get_class(args.class_path)
    model = models.resnet101(weights=None)
    weights_dict = torch.load(args.model_path, map_location='cpu')
    model.load_state_dict(weights_dict)
    model = model.to(device)

    image_files = os.listdir(args.image_path)

    transform = transforms.Compose([
        transforms.Resize((224, 224)),  # 将图像的大小调整为224x224像素
        transforms.ToTensor(),  # 将图像从PIL.Image格式转换为PyTorch张量格式。
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # 对图像进行归一化，使其具有指定的均值和标准差。
    ])

    for image_file in image_files:
        image = Image.open(os.path.join(args.image_path, image_file))
        image = transform(image).unsqueeze(dim=0)

        model.eval()
        with torch.no_grad():
            image = image.to(device)
            output = model(image)
            _, predicted = torch.max(output, 1)
            txt = f'{image_file}的预测结果为:{classes_dict[predicted.item()]}'
            with open('output/predict.txt', "a") as f:
                f.write(txt + "\n")
            print(txt)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('--image_path', default=r'D:\Code\deep-learning-algorithms\KAN\data\val')
    parser.add_argument('--model_path', default=r'output/best_model.pth')
    parser.add_argument('--class_path', default='classes.txt')
    args = parser.parse_args()
    print(args)
    main()

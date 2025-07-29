import os

import numpy as np
from PIL import Image
from torch.utils.data import Dataset, DataLoader, ConcatDataset
from torchvision import transforms


class CustomDataset(Dataset):
    def __init__(self, root_dir, transform, class_to_label=None):
        self.root_dir = root_dir
        self.transform = transform or transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        self.class_to_label = class_to_label if class_to_label is not None else {}
        self.images = [f for f in os.listdir(root_dir) if f.endswith(('.bmp', '.jpg', '.png'))]

        # 如果没有提供class_to_label字典，我们在这里创建它
        if not self.class_to_label:
            self._create_class_to_label_mapping()
            self.idx_to_labels = {i: cls_name for i, cls_name in enumerate(self.class_to_label)}

    def _create_class_to_label_mapping(self):
        # 假设类别是从0开始编号的连续整数
        self.classes = sorted(set([filename.split('_')[0] for filename in self.images]))
        self.class_to_label = {cls: i for i, cls in enumerate(self.classes)}

    def get_class_to_label(self):
        return self.class_to_label

    def __len__(self):
        return len(self.images)

    def save_label_mapping(self):
        save_dir = os.path.join(os.path.dirname(self.root_dir))
        np.save(os.path.join(save_dir, 'idx_to_labels.npy'), self.idx_to_labels)
        np.save(os.path.join(save_dir, 'classes_to_idx.npy'), self.class_to_label)

    def __getitem__(self, idx):
        # 获取图片路径
        image_path = os.path.join(self.root_dir, self.images[idx])
        # 打开图片并转换为RGB格式
        # image = Image.open(image_path).convert('RGB')
        image = Image.open(image_path)
        # 如果有变换，则进行变换
        if self.transform:
            image = self.transform(image)

        # 提取文件名中的类别
        base_filename = os.path.splitext(self.images[idx])[0]
        class_name = base_filename.split('_')[0]
        # 将类别转换为标签
        label = self.class_to_label[class_name]

        return image, label


def create_dataloaders(data_path, batch_size, transform=transforms.ToTensor(), num_workers=0, subset=False,
                       train_shuffle=True):
    # 训练集数据加载器
    train_dir = os.path.join(data_path, 'train')
    train_dataset = CustomDataset(root_dir=train_dir, transform=transform)
    # 初始化验证集Dataset
    validation_dir = os.path.join(data_path, 'val')  # 替换为你的验证集图片目录
    validation_dataset = CustomDataset(root_dir=validation_dir, transform=transform)
    if not subset:
        train_loader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=train_shuffle,
                                  num_workers=num_workers)
        val_loader = DataLoader(dataset=validation_dataset, batch_size=batch_size, shuffle=False)
        return train_loader, val_loader
    else:
        dataset = ConcatDataset([train_dataset, validation_dataset])
        dataloader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=False)
        return dataloader

# if __name__ == '__main__':
    # data = CustomDataset(root_dir=r'D:\Code\0-data\3-故障诊断数据集\defect\train', transform=transforms.Compose([]))
    # data.save_label_mapping()

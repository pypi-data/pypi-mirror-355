import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
import torch.nn.functional as F
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
import numpy as np
# import seaborn as sns

train_accuracies = []
val_accuracies = []
train_losses = []
val_losses = []
# 自定义训练数据集类
class CustomTrainDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir
        # 将数据增强和转换组合在一起
        self.transform = transform or transforms.Compose([
            transforms.RandomResizedCrop(224),  # 随机裁剪到224x224
            transforms.RandomHorizontalFlip(),   # 随机水平翻转
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        # 获取root_dir目录下的所有文件夹，并将其存入self.classes列表中
        self.classes = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
        # 将self.classes中的文件夹名称作为键，索引值作为值，存入self.class_to_idx字典中
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
        # 构建图像路径和标签的列表
        self.images = []
        for cls_name in self.classes:
            dir_path = os.path.join(self.root_dir, cls_name)
            for img_name in os.listdir(dir_path):
                if img_name.endswith('.jpg'):
                    self.images.append((os.path.join(dir_path, img_name), self.class_to_idx[cls_name]))

   # 定义一个名为__len__的方法，用于返回images列表的长度
    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        # 获取图片路径和标签
        image_path, label = self.images[idx]
        # 以RGB模式打开图片
        image = Image.open(image_path).convert('RGB')
        # 如果进行了变换，则进行变换
        if self.transform:
            image = self.transform(image)
        # 返回图片和标签
        return image, label


# 自定义验证数据集类
# 自定义Dataset类
class CustomValidationDataset(Dataset):
    def __init__(self, root_dir, transform=None, class_to_label=None):
        self.root_dir = root_dir
        self.transform = transform
        self.class_to_label = class_to_label if class_to_label is not None else {}
        self.images = [f for f in os.listdir(root_dir) if f.endswith('.bmp')]

        # 如果没有提供class_to_label字典，我们在这里创建它
        if not self.class_to_label:
            self._create_class_to_label_mapping()

    def _create_class_to_label_mapping(self):
        # 假设类别是从0开始编号的连续整数
        classes = sorted(set([filename.split('_')[0] for filename in self.images]))
        self.class_to_label = {cls: i for i, cls in enumerate(classes)}

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        # 获取图片路径
        image_path = os.path.join(self.root_dir, self.images[idx])
        # 打开图片并转换为RGB格式
        image = Image.open(image_path).convert('RGB')

        # 如果有变换，则进行变换

        if self.transform:
            image = self.transform(image)

        # 提取文件名中的类别
        base_filename = os.path.splitext(self.images[idx])[0]
        class_name = base_filename.split('_')[0]
        # 将类别转换为标签
        label = self.class_to_label[class_name]

        return image, label

def plot_confusion_matrix(cm, classes,
                              normalize=False,
                              title='Confusion matrix',
                              cmap=plt.cm.Blues):
        """
        绘制混淆矩阵的函数
        这个函数不修改原始数据，但会返回混淆矩阵。
        """
        if normalize:
            cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
            print("Normalized confusion matrix")
        else:
            print('Confusion matrix, without normalization')

        plt.imshow(cm, interpolation='nearest', cmap=cmap)
        plt.title(title)
        plt.colorbar()
        tick_marks = np.arange(len(classes))
        plt.xticks(tick_marks, classes, rotation=45)
        plt.yticks(tick_marks, classes)

        fmt = '.2f' if normalize else 'd'
        #用于判断变量normalize的值。如果normalize为True，则将格式化字符串.2f赋值给变量fmt；否则，将格式化字符串'd'赋值给变量fmt。
        #其中，.2f表示保留两位小数，'d'表示以十进制形式显示。
        thresh = cm.max() / 2.
        for i, j in np.ndindex(cm.shape):
            plt.text(j, i, format(cm[i, j], fmt),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")

        plt.tight_layout()
        plt.ylabel('True label')
        plt.xlabel('Predicted label')

    # 数据预处理


transform = transforms.Compose([
    transforms.Resize((224, 224)),#将图像的大小调整为224x224像素
    transforms.ToTensor(),#将图像从PIL.Image格式转换为PyTorch张量格式。
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]), #对图像进行归一化，使其具有指定的均值和标准差。
])

# 初始化验证集Dataset
# 定义验证集图片目录
validation_dir = r'D:\Code\data\data\val'  # 替换为你的验证集图片目录
# 创建验证集数据集对象
validation_dataset = CustomValidationDataset(root_dir=validation_dir, transform=transform)

# 创建DataLoader
validation_loader = DataLoader(dataset=validation_dataset, batch_size=16, shuffle=False)

# 数据预处理
transform1 = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# 训练集数据加载器

# 定义训练集的目录
train_dir = r'D:\Code\data\data\train'
# 创建自定义训练数据集类
train_dataset = CustomTrainDataset(root_dir=train_dir, transform=transform1)
# 创建数据加载器
train_loader = DataLoader(dataset=train_dataset, batch_size=16, shuffle=True)

# 使用resnet18、googlenet、vgg16、alexnet四种模型训练，其中vgg16没有全连接层

model_leibie=input('请输入模型类别：')

if model_leibie=='resnet18':
   # 加载ResNet-18预训练模型
   model = models.resnet18(pretrained=True)

elif model_leibie=='googlenet':
    # 加载googlenet预训练模型
    model = models.googlenet(pretrained=True)

elif model_leibie=='vgg16':
    #加载vgg16模型
    model = models.vgg16(pretrained=True)

elif model_leibie=='alexnet':
    #加载alexnet模型
    model = models.alexnet(pretrained=True)

# 设置设备
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(device)
model = model.to(device)

# 损失函数和优化器
criterion = nn.CrossEntropyLoss()  #定义了损失函数为交叉熵损失函数。
optimizer = optim.Adam(model.parameters(), lr=0.001,weight_decay=0.001) #定义了优化器为Adam优化器，学习率为0.001，权重衰减为0.001。

# 定义学习率衰减的调度器
# 使用StepLR学习率调度器，设置学习率下降的步长为1，下降率为0.1
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.1)

# 训练模型
num_epochs = 20
for epoch in range(num_epochs):
    # 训练模型
    model.train()
    running_loss = 0.0
    running_corrects_train = 0
    total_samples_train = 0

    for images, labels in train_loader:
        # 将数据转移到设备
        images, labels = images.to(device), labels.to(device)
        # 梯度清零
        optimizer.zero_grad()
        # 前向传播
        outputs = model(images)
        # 计算损失
        loss = criterion(outputs, labels)
        # 反向传播
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * images.size(0)   # 计算训练损失
        _, preds = torch.max(outputs, 1)    # 计算预测值
        running_corrects_train += torch.sum(preds == labels).item()         # 计算训练准确率
        total_samples_train += labels.size(0) # 计算训练样本总数

    # 计算训练损失和训练准确率
    epoch_loss = running_loss / total_samples_train
    train_accuracy = running_corrects_train / total_samples_train
    print(f'Epoch {epoch + 1}/{num_epochs}, Loss: {epoch_loss:.4f}, Train Accuracy: {train_accuracy:.4f}')

    # 更新学习率
    scheduler.step()

    # 收集所有预测结果和真实标签
    all_preds = []
    all_labels = []

    # 验证模型
    model.eval()
    running_corrects_val = 0
    total_samples_val = 0
    running_val_loss = 0

    with torch.no_grad():
        # 遍历验证集加载器
        for images, labels in validation_loader:
            images, labels = images.to(device), labels.to(device)    # 将图片和标签转移到设备

            outputs = model(images)  # 运行模型
            loss = criterion(outputs, labels)# 计算损失
            running_val_loss += loss.item() * images.size(0) # 累加损失

            _, preds = torch.max(outputs, 1) # 获取预测结果
            running_corrects_val += torch.sum(preds == labels).item() # 累加正确预测的样本数
            total_samples_val += labels.size(0)  # 累加总样本数

            # 将预测结果和真实标签添加到列表
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # 计算验证准确率、验证损失
    val_loss = running_val_loss / total_samples_val
    val_accuracy = (running_corrects_val / total_samples_val)
    print(f'Validation Loss: {val_loss:.4f}, Validation Accuracy: {val_accuracy:.4f}')

    # 然后在训练循环中，每次epoch结束后添加
    train_accuracies.append(train_accuracy)
    val_accuracies.append(val_accuracy)
    # 将验证损失添加到列表
    val_losses.append(val_loss)
    # 将训练损失添加到列表
    train_losses.append(epoch_loss)

# 计算混淆矩阵
cm = confusion_matrix(all_labels, all_preds, labels=np.arange(len(train_dataset.classes)))

# 绘制混淆矩阵
plt.figure()
plot_confusion_matrix(cm, classes=train_dataset.classes, title='Confusion matrix')


# 在所有epoch结束后添加
plt.figure(figsize=(12, 6))
plt.plot(range(1, num_epochs + 1), train_accuracies, label='Training Accuracy')
plt.plot(range(1, num_epochs + 1), val_accuracies, label='Validation Accuracy')
plt.title('Accuracy over epochs')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()
plt.grid(True)

# 保存图像到指定文件夹

plt.savefig('D:/data/accuracy_plot.jpg')  # 确保使用正确的引号
# 绘制训练和验证损失
plt.figure(figsize=(12, 6))
plt.plot(range(1, num_epochs + 1), train_losses, label='Training Loss')
plt.plot(range(1, num_epochs + 1), val_losses, label='Validation Loss')
plt.title('Loss over epochs')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.grid(True)
plt.show()
# 保存模型
torch.save(model.state_dict(), 'model.pth')

print('Training complete')
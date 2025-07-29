import argparse
import os

import torch
from sklearn.metrics import classification_report
from torch.utils.data import DataLoader
from torchvision import transforms
from tqdm import tqdm

from yms_class.models.AlexNet import AlexNet
from yms_class.tools.dataset import CustomDataset
from yms_class.tools.plotting import plot_confusion_matrix


def main(args):
    all_predictions = []
    all_labels = []
    output_dir = args.output_dir
    results_file = os.path.join(output_dir, 'test_results.txt')
    result_info = ['accuracy', 'precision', 'recall', 'f1-score']

    column_widths = [8, 9, 6, 8]  # 根据实际需要调整宽度
    device = torch.device('cuda:0' if torch.cuda.is_available() else "cpu")
    print("Using {} device training.".format(device.type))
    data_transform = transforms.Compose([
        transforms.Resize((224, 224)),  # 将图像的大小调整为224x224像素
        transforms.ToTensor(),  # 将图像从PIL.Image格式转换为PyTorch张量格式。
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # 对图像进行归一化，使其具有指定的均值和标准差。
    ])

    data_path = os.path.join(args.data_dir, 'test')
    batch_size = args.batch_size

    test_dataset = CustomDataset(root_dir=data_path, transform=data_transform)
    test_loader = DataLoader(dataset=test_dataset, batch_size=batch_size, shuffle=False)

    model = AlexNet(num_classes=4)
    weights_path = args.weights_path
    weights_dict = torch.load(weights_path, map_location='cpu', weights_only=True)
    model.load_state_dict(weights_dict)
    model = model.to(device)

    model.eval()
    test_iterator = tqdm(test_loader)
    with torch.no_grad():
        for images, labels in test_iterator:
            images = images.to(device)
            labels = labels.to(device)
            outputs = model(images)

            _, predicted = torch.max(outputs, 1)
            all_predictions.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    plot_confusion_matrix(all_labels=all_labels, all_predictions=all_predictions,
                          classes=test_dataset.classes, path=output_dir, name='test_confusion_matrix.png')
    result = classification_report(y_true=all_labels, y_pred=all_predictions,
                                   target_names=test_dataset.classes, digits=4, output_dict=True)
    print(result)


def parse_args(args=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data_dir', type=str, default=r'D:\Code\deep-learning-algorithms\KAN\data\工况1')
    parser.add_argument('--output_dir', type=str, default=r'output')
    parser.add_argument('--batch_size', default=20, type=int, metavar='N', help='batch size when training.')
    parser.add_argument('--weights_path', default=r'output/best_model.pth',
                        help='pre-trained path')
    return parser.parse_args(args if args else [])


if __name__ == '__main__':
    opts = parse_args()
    print(opts)
    os.makedirs(opts.output_dir)
    main(opts)

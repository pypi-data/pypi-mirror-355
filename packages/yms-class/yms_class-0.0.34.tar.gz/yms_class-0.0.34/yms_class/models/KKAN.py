import torch
from torch import nn

from yms_class.convolution.cov import KANConvolution
from yms_class.kan_convolutional.KANConv import KAN_Convolutional_Layer
from yms_class.models.CNN import CNN
from yms_class.tools.tool import count_model_params


class KKAN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            KAN_Convolutional_Layer(in_channels=3, out_channels=4, kernel_size=(3, 3), padding=(1, 1),
                                    grid_size=5),
            KAN_Convolutional_Layer(in_channels=4, out_channels=8, kernel_size=(3, 3), padding=(1, 1),
                                    grid_size=5),
            nn.MaxPool2d(2),
            KAN_Convolutional_Layer(in_channels=8, out_channels=16, kernel_size=(3, 3), padding=(1, 1),
                                    grid_size=5),
            KAN_Convolutional_Layer(in_channels=16, out_channels=32, kernel_size=(3, 3), padding=(1, 1),
                                    grid_size=5),
            nn.MaxPool2d(2),
        )
        self.classifier = nn.Sequential(
            nn.Linear(32 * 8 * 8, 2048),
            nn.ReLU(),
            nn.Linear(2048, 1024),
            nn.ReLU(),
            nn.Linear(1024, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

class CCNN(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 4, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(4, 8, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(8, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2)
        )
        self.classifier = nn.Sequential(
            nn.Linear(32 * 8 * 8, 2048),
            nn.ReLU(),
            nn.Linear(2048, 1024),
            nn.ReLU(),
            nn.Linear(1024, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x


class KANCov(nn.Module):
    def __init__(self, num_classes=10):
        super().__init__()
        self.features = nn.Sequential(
            KANConvolution(in_channels=3, out_channels=8, kernel_size=3, padding=1),
            nn.MaxPool2d(kernel_size=3, stride=2),
            KANConvolution(in_channels=8, out_channels=16, kernel_size=3, padding=1),
            KANConvolution(in_channels=16, out_channels=32, kernel_size=3, padding=1),
            KANConvolution(in_channels=32, out_channels=48, kernel_size=3, padding=1),
            nn.MaxPool2d(kernel_size=3, stride=2),
        )
        self.classifier = nn.Sequential(
            nn.Linear(48 * 7 * 7, 2048),
            nn.ReLU(),
            nn.Linear(2048, 1024),
            nn.ReLU(),
            nn.Linear(1024, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x

if __name__ == '__main__':
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = KANCov().to(device)
    # kan_num = count_model_params(kan)
    # print(f'KAN卷积的参数量:{kan_num}')
    y = torch.randn(1, 3, 32, 32).to(device)
    z = model(y)
    print(z)

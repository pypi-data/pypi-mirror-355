# 定义残差块
import torch
from torch import nn


class ResidualBlock(nn.Module):
    def __init__(self, channels):
        super().__init__()
        self.res = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(channels),
            nn.ReLU(),
            nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(channels),
            nn.ReLU(),
        )

    def forward(self, x):
        residual = x
        out = self.res(x)
        return out + residual


# 编码器
class Encoder(nn.Module):
    def __init__(self, in_channels=3,mask_ratio=0.3):
        super().__init__()
        self.mask_ratio = mask_ratio
        # Conv1 + ResidualBlock1
        self.conv1 = nn.Sequential(
            nn.Conv2d(in_channels, 16, 3, stride=2, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            ResidualBlock(16)
        )
        # Conv2 + ResidualBlock2
        self.conv2 = nn.Sequential(
            nn.Conv2d(16, 32, 3, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            ResidualBlock(32)
        )
        # Conv3 + ResidualBlock3
        self.conv3 = nn.Sequential(
            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            ResidualBlock(64)
        )
        # Conv4 + ResidualBlock4
        self.conv4 = nn.Sequential(
            nn.Conv2d(64, 128, 3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            ResidualBlock(128)
        )
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(128 * 20 * 20, 4096)

    def add_noise(self, x):
        if self.training:
            mask = (torch.rand_like(x) > self.mask_ratio).float()
            return x * mask
        return x

    def forward(self, x):
        x = self.add_noise(x)
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = self.conv4(x)
        x = self.flatten(x)
        x = self.fc(x)
        return x


# 解码器
class Decoder(nn.Module):
    def __init__(self, out_channels=3):
        super().__init__()
        self.fc = nn.Linear(4096, 128*20*20)
        self.unFlatten = nn.Unflatten(1, (128, 20, 20))

        self.deConv = nn.Sequential(
            # DeConv1
            nn.ConvTranspose2d(128, 64, 3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            # DeConv2
            nn.ConvTranspose2d(64, 32, 3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            # DeConv3
            nn.ConvTranspose2d(32, 16, 3, stride=2, padding=1, output_padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            # DeConv4 (输出层)
            nn.ConvTranspose2d(16, out_channels, 3, stride=2, padding=1, output_padding=1),
        )

    def forward(self, x):
        x = self.fc(x)
        x = self.unFlatten(x)
        x = self.deConv(x)
        return torch.sigmoid(x)  # 假设输出在[0,1]范围
        # return x


class DRCAE(nn.Module):
    def __init__(self, in_channels=3, out_channels=3, mask_ratio=0.3):
        super().__init__()
        self.encoder = Encoder(in_channels, mask_ratio)
        self.decoder = Decoder(out_channels)

    def forward(self, x):
        x = self.encoder(x)
        x = self.decoder(x)
        return x

    def save(self, path):
        torch.save(self.encoder, path)

    def save_decoder(self, path):
        torch.save(self.decoder.state_dict(), path)


if __name__ == '__main__':
    model = DRCAE(in_channels=1, out_channels=1)
    train_input = torch.randn((1, 1, 160, 160))
    output = model(train_input)
    print(output.size())

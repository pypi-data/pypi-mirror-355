import argparse
import os

import torch
from torch.nn import MSELoss
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torchvision import transforms

from yms_class.models.DECAE import DRCAE
from yms_class.tools.dataset import create_dataloaders
from yms_class.tools.plotting import plot_all_metrics
from yms_class.tools.tool import append_to_results_file, initialize_results_file, make_save_dirs
from yms_class.tools.train_eval_utils import train_decae_one_epoch


def main(args):
    save_dir = args.save_dir
    img_dir, model_dir = make_save_dirs(save_dir)

    results_file = os.path.join(save_dir, 'decae_results.txt')
    decae_column_order = ['epoch', 'train_losses', 'val_losses', 'lrs']
    initialize_results_file(results_file, decae_column_order)
    custom_column_widths = {'epoch': 5, 'train_loss': 12, 'val_loss': 10, 'lr': 3}

    device = torch.device('cuda:0' if torch.cuda.is_available() else "cpu")
    print("Using {} device training.".format(device.type))
    if args.num_workers:
        num_workers = max(min(os.cpu_count() - 1, args.batch_size), 0)
    else:
        num_workers = 0
    print(f'use {num_workers} workers')
    data_transform = transforms.Compose([
        transforms.Resize((160, 160)),  # 将图像的大小调整为224x224像素
        transforms.ToTensor(),  # 将图像从PIL.Image格式转换为PyTorch张量格式。
    ])
    train_loader, val_loader = create_dataloaders(args.data_dir, args.batch_size,
                                                  num_workers=num_workers, transform=data_transform)
    metrics = {'train_losses': [], 'val_losses': [], 'lrs': []}

    model = DRCAE(in_channels=1, out_channels=1).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    lr_scheduler = ReduceLROnPlateau(optimizer, 'min', factor=0.1, patience=4, min_lr=1e-9)
    criterion = MSELoss()
    best = 1e8
    for epoch in range(0, args.epochs):
        result = train_decae_one_epoch(model, train_loader, val_loader, device, optimizer, criterion, epoch)
        lr = lr_scheduler.get_last_lr()[0]
        lr_scheduler.step(result['val_loss'])

        metrics['val_losses'].append(result['val_loss'])
        metrics['train_losses'].append(result['train_loss'])
        metrics['lrs'].append(lr)
        result.update({'lr': lr})

        append_to_results_file(results_file, result, decae_column_order,
                               custom_column_widths=custom_column_widths)

        save_file = {
            'epoch': epoch,
            'model_state_dict': model,
            'optimizer_state_dict': optimizer,
            'lr_scheduler_state_dict': lr_scheduler,
        }
        torch.save(save_file, os.path.join(model_dir, 'last_decoder.pt'))
        if result['val_loss'] < best:
            best = result['val_loss']
            model.save(os.path.join(model_dir, 'decoder.pt'))

    plot_all_metrics(metrics, args.epochs, 'decoder', img_dir)
    os.remove(os.path.join(model_dir, 'last_decoder.pt'))


def parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, default=r'D:\Code\0-data\滚刀磨损\Hobwear\scale_5')
    parser.add_argument('--save_dir', type=str, default=r'D:\Code\deep-learning-code\output\scale_5')
    parser.add_argument('--epochs', type=int, default=4)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--num_workers', type=bool, default=False)
    return parser.parse_args(args if args else [])


if __name__ == '__main__':
    opts = parse_args()
    print(opts)
    main(opts)

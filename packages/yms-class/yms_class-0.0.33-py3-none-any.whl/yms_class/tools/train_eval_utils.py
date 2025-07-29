import sys

import torch
from sklearn.metrics import accuracy_score, classification_report
from tqdm import tqdm


def train_one_epoch(model, train_loader, device, optimizer, criterion, epoch):
    mean_loss = torch.zeros(1).to(device)
    all_predictions = []
    all_labels = []
    model.train()
    train_iterator = tqdm(train_loader, file=sys.stdout, desc=f'the {epoch + 1} epoch is training....', colour='blue')
    for step, (images, labels) in enumerate(train_iterator):
        # 将数据转移到设备
        images, labels = images.to(device), labels.to(device)
        # 梯度清0
        optimizer.zero_grad()
        # 前向传播
        outputs = model(images)
        # 计算损失
        loss = criterion(outputs, labels)
        # 反向传播
        loss.backward()
        # 更新参数
        optimizer.step()

        mean_loss = (mean_loss * step + loss.detach()) / (step + 1)
        _, predicted = torch.max(outputs, 1)
        # 设置进度条
        train_iterator.set_postfix(loss=loss.item(), mean_loss=mean_loss.item())
        all_predictions.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    train_accuracy = accuracy_score(y_true=all_labels, y_pred=all_predictions)
    return mean_loss.item(), train_accuracy


@torch.no_grad()
def eval_one_epoch(model, val_loader, device, criterion, epoch):
    result = {"y_pred": [], "y_true": [], 'val_loss': 0.}
    val_loss = torch.zeros(1).to(device)
    model.eval()
    val_iterator = tqdm(val_loader, file=sys.stdout, desc=f'{epoch + 1} epoch is validation...', colour='GREEN')
    for step, (images, labels) in enumerate(val_iterator):
        # 将数据转移到设备
        images, labels = images.to(device), labels.to(device)
        # 计算结果
        outputs = model(images)
        # 计算损失
        loss = criterion(outputs, labels)
        # 计算数据集上的全部损失
        val_loss = (val_loss * step + loss.detach()) / (step + 1)
        # 计算预测正确的样本
        _, predicted = torch.max(outputs, 1)
        val_iterator.set_postfix(loss=loss.item(), val_loss=val_loss.item())

        result["y_pred"].extend(predicted.cpu().numpy())
        result["y_true"].extend(labels.cpu().numpy())

    result['val_loss'] = val_loss.item()
    return result


def train_decae_one_epoch(model, train_loader, val_loader, device, optimizer, criterion, epoch):
    result = {'train_loss': 0., 'val_loss': 0., 'epoch': 0}
    train_loss = torch.zeros(1).to(device)
    model.train()
    train_iterator = tqdm(train_loader, file=sys.stdout, colour='yellow')
    for step, (images, label) in enumerate(train_iterator):
        images = images.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, images)

        loss.backward()
        optimizer.step()

        train_loss = (train_loss * step + loss.detach()) / (step + 1)
        train_iterator.set_postfix(loss=loss.item(), mean_loss=train_loss.item())

    print(f'the epoch {epoch + 1} train loss is {train_loss.item():.6f}')
    val_loss = torch.zeros(1).to(device)
    model.eval()
    val_iterator = tqdm(val_loader, file=sys.stdout, colour='MAGENTA')
    with torch.no_grad():
        for step, (images, label) in enumerate(val_iterator):
            images = images.to(device)

            outputs = model(images)
            loss = criterion(outputs, images)
            val_loss = (val_loss * step + loss.detach()) / (step + 1)

            val_iterator.set_postfix(loss=loss.item(), mean_loss=val_loss.item())
    print(f'the epoch {epoch + 1} val loss is {val_loss.item():.6f}')
    result['train_loss'] = train_loss.item()
    result['val_loss'] = val_loss.item()
    result['epoch'] = epoch + 1
    return result


def calculate_results(y_true, y_pred, classes):
    results = classification_report(y_true, y_pred, target_names=classes, output_dict=True, digits=4)
    return results

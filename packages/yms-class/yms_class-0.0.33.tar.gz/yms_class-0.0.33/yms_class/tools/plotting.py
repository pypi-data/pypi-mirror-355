import os
from typing import Union, List

import numpy as np
from matplotlib import pyplot as plt, rcParams
from sklearn.manifold import TSNE
from sklearn.metrics import ConfusionMatrixDisplay, roc_curve, auc, precision_recall_curve
from sklearn.preprocessing import label_binarize


# def plot_confusion_matrix(cm, classes,
#                           save_path='confusion_matrix_D1.png',
#                           normalize=False,
#                           title='Confusion matrix',
#                           cmap=plt.cm.Blues):
#     """
#         绘制混淆矩阵的函数
#         这个函数不修改原始数据，但会返回混淆矩阵。
#         """
#     plt.figure()
#     if normalize:
#         cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
#         print("Normalized confusion matrix")
#     else:
#         print('Confusion matrix, without normalization')
#
#     plt.imshow(cm, interpolation='nearest', cmap=cmap)
#     plt.title(title)
#     plt.colorbar()
#     tick_marks = np.arange(len(classes))
#     plt.xticks(tick_marks, classes, rotation=45)
#     plt.yticks(tick_marks, classes)
#
#     fmt = '.2f' if normalize else 'd'
#     # 用于判断变量normalize的值。如果normalize为True，则将格式化字符串.2f赋值给变量fmt；否则，将格式化字符串'd'赋值给变量fmt。
#     # 其中，.2f表示保留两位小数，'d'表示以十进制形式显示。
#     thresh = cm.max() / 2.
#     for i, j in np.ndindex(cm.shape):
#         plt.text(j, i, format(cm[i, j], fmt),
#                  horizontalalignment="center",
#                  color="white" if cm[i, j] > thresh else "black")
#
#     plt.tight_layout()
#     plt.ylabel('True label')
#     plt.xlabel('Predicted label')
#     plt.savefig(save_path)
#     plt.close()

def plot_confusion_matrix(all_labels,
                          all_predictions,
                          classes,
                          path,
                          name='confusion_matrix.png',
                          normalize=None,
                          cmap=plt.cm.Blues,
                          ):
    ConfusionMatrixDisplay.from_predictions(all_labels,
                                            all_predictions,
                                            display_labels=classes,
                                            cmap=cmap,
                                            normalize=normalize,
                                            xticks_rotation=45
                                            )
    plt.savefig(os.path.join(path, name), dpi=500)
    plt.close()


def plot_multi_class_curves(y_true, y_pred, target_names, save):
    # 将多分类标签转换为二进制标签（One - vs - Rest）
    n_classes = len(set(target_names))
    y_true_bin = label_binarize(y_true, classes=range(n_classes))
    y_pred_bin = label_binarize(y_pred, classes=range(n_classes))

    # 计算每个类别的精确率 - 召回率曲线和 AUC
    precision = dict()
    recall = dict()
    auc_scores = dict()

    for i in range(n_classes):
        precision[i], recall[i], _ = precision_recall_curve(y_true_bin[:, i], y_pred_bin[:, i])
        auc_scores[i] = auc(recall[i], precision[i])

    # 绘制精确率 - 召回率曲线
    plt.figure()
    # 使用更丰富的颜色映射来应对类别数不确定的情况
    cmap = plt.get_cmap('tab10')
    for i in range(n_classes):
        color = cmap(i % 10)  # 循环使用颜色映射中的颜色
        plt.plot(recall[i], precision[i], color=color, lw=2,
                 label=f'{target_names[i]}:{auc_scores[i]:0.4f}')

    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.legend(loc="best")
    # 确保保存路径存在
    if not os.path.exists(save):
        os.makedirs(save)
    plt.savefig(os.path.join(save, 'precision_recall_curve.png'), dpi=500)
    plt.close()

    # 计算每个类别的 ROC 曲线和 AUC
    fpr = dict()
    tpr = dict()
    roc_auc = dict()

    for i in range(n_classes):
        fpr[i], tpr[i], _ = roc_curve(y_true_bin[:, i], y_pred_bin[:, i])
        roc_auc[i] = auc(fpr[i], tpr[i])

    # 绘制 ROC 曲线
    plt.figure()
    for i in range(n_classes):
        color = cmap(i % 10)  # 循环使用颜色映射中的颜色
        plt.plot(fpr[i], tpr[i], color=color, lw=2,
                 label=f'{target_names[i]}:{roc_auc[i]:0.4f}')

    plt.plot([0, 1], [0, 1], 'k--', lw=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.0])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.legend(loc="best")
    plt.savefig(os.path.join(save, 'roc_curve.png'), dpi=500)
    plt.close()


def plot_all_metrics(metrics_dict, num_epochs, img_name, save_path, plot_metric=False):
    """
    绘制训练指标曲线

    参数：
        metrics_dict: 包含指标数据的字典，键为指标名称，值为一个列表
        num_epochs: 训练的总轮数
        save_path: 保存图像的路径，默认为 'metrics.png'
    """
    # 检查是否存在 train_losses 和 val_losses
    has_train_loss = 'train_losses' in metrics_dict
    has_val_loss = 'val_losses' in metrics_dict

    # 获取指标名称列表，排除 'epoch'
    metric_names = [key for key in metrics_dict.keys() if key != 'epoch']

    # 如果有 train_losses 和 val_losses，添加一个特殊的键
    if has_train_loss and has_val_loss:
        metric_names.append('train_val_loss')

    # 计算子图的行数和列数，使得 m*n 最接近 metric_names 的数量
    num_metrics = len(metric_names)
    m = int(np.ceil(np.sqrt(num_metrics)))
    n = int(np.ceil(num_metrics / m))

    # 创建子图
    fig, axes = plt.subplots(m, n, figsize=(12 * n, 6 * m))
    axes = axes.flatten()  # 将二维数组的 axes 展平为一维

    # 绘制每个指标的曲线
    for i, name in enumerate(metric_names):
        ax = axes[i]

        if name == 'train_val_loss':
            # 绘制 train_losses 和 val_losses 在同一张图
            train_loss = metrics_dict['train_losses']
            val_loss = metrics_dict['val_losses']
            ax.plot(range(1, num_epochs + 1), train_loss, label='Training Loss')
            ax.plot(range(1, num_epochs + 1), val_loss, label='Validation Loss')
            ax.set_title('Loss over epochs')
        else:
            # 绘制其他指标
            metric = metrics_dict[name]
            ax.plot(range(1, num_epochs + 1), metric, label=f'{name}')
            ax.set_title(f'{name} over epochs')

        ax.set_xlabel('Epochs')
        ax.set_ylabel(f'{name}')
        ax.legend()
        ax.grid(True)

    # 删除多余的子图
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    # 调整布局并保存图像
    plt.tight_layout()
    plt.savefig(os.path.join(save_path, f'{img_name}_metrics.png'), dpi=500)
    plt.close()
    if plot_metric:
        # 为每个指标单独绘制一张图
        for name in metric_names:
            plt.figure(figsize=(12, 6))
            if name == 'train_val_loss':
                # 绘制 train_losses 和 val_losses 在同一张图
                train_loss = metrics_dict['train_losses']
                val_loss = metrics_dict['val_losses']
                plt.plot(range(1, num_epochs + 1), train_loss, label='Training Loss')
                plt.plot(range(1, num_epochs + 1), val_loss, label='Validation Loss')
                plt.title('Loss over epochs')
            else:
                # 绘制其他指标
                metric = metrics_dict[name]
                plt.plot(range(1, num_epochs + 1), metric, label=f'{name}')
                plt.title(f'{name} over epochs')

            plt.xlabel('Epochs')
            plt.ylabel(f'{name}')
            plt.legend()
            plt.grid(True)
            plt.savefig(os.path.join(save_path, f'{img_name}_{name}.png'), dpi=500)
            plt.close()


def plot_metrics(metric1, metric2, num_epochs, name, save_path='metrics.png'):
    plt.figure(figsize=(12, 6))
    plt.plot(range(1, num_epochs + 1), metric1, label=f'Training {name}')
    plt.plot(range(1, num_epochs + 1), metric2, label=f'Validation {name}')
    plt.title(f'{name} over epochs')
    plt.xlabel('Epochs')
    plt.ylabel(f'{name}')
    plt.legend()
    plt.grid(True)
    plt.savefig(save_path, dpi=500)
    plt.close()


def plot_single(met, num_epochs, name, save_path='metrics.png'):
    plt.figure(figsize=(12, 6))
    plt.plot(range(1, num_epochs + 1), met)
    plt.title(f'{name} over epochs')
    plt.xlabel('Epochs')
    plt.ylabel(f'{name}')
    plt.grid(True)
    plt.savefig(save_path, dpi=500)
    plt.close()


def plot_data_from_files(file_paths, exclude_headers=None, save_path='metrics.png'):
    """
    Plot data from multiple text files, excluding specified headers, with a fixed 2 rows layout.
    Use folder name as label if file names are consistent, otherwise use file name.

    Args:
    - file_paths (list): A list of file paths to read data from.
    - exclude_headers (list): A list of headers to exclude from plotting.
    """
    # 设置支持中文的字体
    rcParams['font.family'] = 'Microsoft YaHei'  # Windows系统
    # rcParams['font.family'] = 'PingFang SC'  # macOS系统
    rcParams['axes.unicode_minus'] = False  # 正确显示负号
    if exclude_headers is None:
        exclude_headers = ['epoch', 'lr']  # 默认排除的头部

    # 初始化一个列表来存储所有数据
    all_data = []

    # 处理每个文件
    for path in file_paths:
        data = {}
        with open(path, 'r') as file:
            headers = file.readline().strip().split('\t')
            for header in headers:
                data[header] = []
            for line in file:
                values = line.strip().split('\t')
                for header, value in zip(headers, values):
                    data[header].append(float(value))
        all_data.append(data)

    # 提取共同的epochs
    epochs = all_data[0]['epoch']  # 假设所有文件都有相同的epochs

    # 创建子图
    num_metrics = len([m for m in all_data[0].keys() if m not in exclude_headers])
    num_cols = (num_metrics + 1) // 2 + (1 if num_metrics % 2 else 0)  # 计算列数
    fig, axs = plt.subplots(2, num_cols, figsize=(15, 8), constrained_layout=True)
    axs = axs.flatten()  # 展平数组以便更容易迭代

    # 检查文件名是否一致，以确定使用文件名还是文件夹名作为标签
    file_names = [os.path.basename(path) for path in file_paths]
    unique_names = set(file_names)
    if len(unique_names) == 1:
        labels = [os.path.basename(os.path.dirname(path)) for path in file_paths]
    else:
        labels = file_names

    # 绘制每个指标的曲线图
    for i, key in enumerate([m for m in all_data[0].keys() if m not in exclude_headers]):
        for j, data in enumerate(all_data):
            axs[i].plot(epochs, data[key], label=f'{labels[j]} {key}', color=f'C{j}')
        axs[i].set_title(f'{key} over Epochs')
        axs[i].set_xlabel('Epoch')
        axs[i].set_ylabel(key)
        axs[i].legend()

    # 隐藏多余的子图
    for i in range(num_metrics, len(axs)):
        axs[i].axis('off')

    # 显示图表
    plt.savefig(save_path, dpi=500)
    plt.close()


def visualize_features(
        features: Union[List[List[float]], np.ndarray],
        labels: Union[List[int], np.ndarray],
        class_names: List[str],
        n_components: int = 2,
        perplexity: int = 30,
        learning_rate: float = 200.0,
        title: str = "Feature Visualization (t-SNE)",
        save_path: str = None,
        backend: str = "agg",
        markers: Union[str, List[str]] = 'o'
) -> None:
    """
    最终版t-SNE可视化（动态标记适配+警告修复）

    参数:
        markers: 标记形状（自动区分填充/非填充类型）
                 填充标记 (支持白边): 'o','s','^','v','d','p'等
                 非填充标记 (仅颜色): 'x','+','|','_','*'等
                 3D限制: 仅支持 ['o','s','^','v','x','+']（含填充/非填充）
    """
    # 1. 初始化与环境配置
    plt.switch_backend(backend)  # PyCharm兼容后端
    np.random.seed(42)  # 保证可复现性

    # 2. 数据格式校验（严格模式）
    try:
        features = np.asarray(features, dtype=np.float32)
        labels = np.asarray(labels, dtype=np.int32)
    except Exception as e:
        raise TypeError(f"数据格式错误: {str(e)}") from e

    if features.shape[0] != len(labels):
        raise ValueError(f"特征数量({features.shape[0]})与标签数量({len(labels)})不匹配")
    if np.any(labels < 0) or np.max(labels) >= len(class_names):
        raise ValueError(f"标签范围非法: 期望[0,{len(class_names) - 1}], 实际[{np.min(labels)},{np.max(labels)}]")

    # 3. 标记参数校验（含类型/维度校验）
    unique_labels = np.unique(labels)
    n_classes = len(unique_labels)

    if isinstance(markers, str):
        markers = [markers] * n_classes
    elif not isinstance(markers, list) or len(markers) != n_classes:
        raise ValueError(f"markers需为字符串或长度为{class_names}的列表")

    for i, m in enumerate(markers):
        # 3D标记白名单（改为元组） 🌟 修复1
        if n_components == 3 and m not in ('o', 's', '^', 'v', 'x', '+'):  # 元组
            raise ValueError("3D仅支持: o/s/^/v/x/+")
        # 填充标记校验（元组+元组拼接） 🌟 修复2
        if m not in plt.Line2D.filled_markers + ('x', '+', '|', '_', '*'):  # 元组+元组
            raise ValueError(f"未知标记'{m}'，参考Matplotlib文档")

    # 4. T-SNE降维（完整流程含进度显示）
    print(">>> 开始T-SNE降维...")
    tsne = TSNE(
        n_components=n_components,
        perplexity=perplexity,
        learning_rate=learning_rate,
        max_iter=1000,
        random_state=42,
        verbose=1  # 显示训练进度（PyCharm控制台可见）
    )
    reduced = tsne.fit_transform(features)
    print(">>> 降维完成")

    # 5. 颜色与样式准备
    cmap = plt.colormaps['tab10']  # Matplotlib 3.7+推荐
    colors = cmap(unique_labels)  # 按标签索引颜色
    filled_markers = plt.Line2D.filled_markers  # 内置填充标记集合

    # 6. 绘图核心（2D与3D分离实现）
    fig = plt.figure(figsize=(10, 8) if n_components == 2 else (12, 10))

    ax = fig.add_subplot(111)
    if n_components == 2:

        for i, label in enumerate(unique_labels):
            mask = labels == label
            m = markers[i]

            # 动态参数生成（填充/非填充标记区分）
            if m in filled_markers:  # 填充标记（带白边）
                ax.scatter(
                    reduced[mask, 0], reduced[mask, 1],
                    marker=m,
                    facecolors=colors[i],  # 显式指定填充色
                    edgecolors='white',  # 保留白色边缘
                    linewidths=1.2,  # 边缘粗细
                    alpha=0.8,
                    s=60,
                    label=class_names[i]
                )
            else:  # 非填充标记（仅颜色）
                ax.scatter(
                    reduced[mask, 0], reduced[mask, 1],
                    marker=m,
                    color=colors[i],  # 直接控制线条颜色
                    lw=1.5,  # 线条粗细
                    alpha=0.9,
                    s=80,  # 非填充标记适当放大
                    label=class_names[i]
                )

        ax.set(xlabel='t-SNE Dim 1', ylabel='t-SNE Dim 2')

    elif n_components == 3:
        ax = fig.add_subplot(111, projection='3d')
        for i, label in enumerate(unique_labels):
            mask = labels == label
            m = markers[i]

            # 3D特殊处理（填充标记保留白边，非填充仅颜色）
            if m in filled_markers and m in ['o', 's', '^', 'v']:  # 3D填充标记
                ax.scatter(
                    reduced[mask, 0], reduced[mask, 1], reduced[mask, 2],
                    marker=m,
                    facecolors=colors[i],
                    edgecolors='white',
                    linewidths=0.8,  # 3D边缘更细
                    alpha=0.7,
                    s=40,
                    label=class_names[i]
                )
            else:  # 3D非填充标记（x/+）
                ax.scatter(
                    reduced[mask, 0], reduced[mask, 1], reduced[mask, 2],
                    marker=m,
                    color=colors[i],
                    lw=1.2,
                    alpha=0.8,
                    s=50,
                    label=class_names[i]
                )

        ax.set(xlabel='Dim 1', ylabel='Dim 2', zlabel='Dim 3')

    # 7. 通用图表设置
    ax.set_title(title, fontsize=14, pad=20)
    ax.legend(
        title='Classes',
        bbox_to_anchor=(1.05, 1),
        loc='upper left',
        fontsize=11,
        frameon=True,
        framealpha=0.9
    )
    plt.tight_layout(pad=4)  # 防止标签截断

    # 8. 保存/显示（带错误处理）
    if save_path:
        try:
            plt.savefig(
                save_path,
                dpi=500,
                bbox_inches='tight',
                facecolor='white',
                format='png' if '.' not in save_path else None
            )
            print(f"✅ 图片已保存至: {save_path} (尺寸:{fig.get_size_inches()})")
        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")
        finally:
            plt.close(fig)
    elif backend == 'tkagg':
        plt.show()

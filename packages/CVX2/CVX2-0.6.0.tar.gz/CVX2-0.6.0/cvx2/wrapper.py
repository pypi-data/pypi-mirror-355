import numpy as np
from PIL import Image
from pathlib import Path
from sklearn.metrics import classification_report
import torch
from torch import nn
from torch import optim
from torch.utils.data import random_split
from typing import List, Optional, Union, Tuple, Collection
from torch.optim.lr_scheduler import LRScheduler
from torch.utils.data import Dataset, Sampler
from torchvision import transforms
from torchvision.datasets import ImageFolder

from model_wrapper.utils import acc_predict
from model_wrapper import (
    ModelWrapper,
    FastModelWrapper,
    ClassifyModelWrapper,
    FastClassifyModelWrapper,
    SplitClassifyModelWrapper,
    RegressModelWrapper,
    FastRegressModelWrapper,
    SplitRegressModelWrapper,
    log_utils,
    acc_predict_dataset,
    ClassifyMonitor,
)

__all__ = [
    "ModelWrapper",
    "FastModelWrapper",
    "ClassifyModelWrapper",
    "FastClassifyModelWrapper",
    "SplitClassifyModelWrapper",
    "ImageClassifyModelWrapper",
    "SplitImageClassifyModelWrapper",
    "RegressModelWrapper",
    "FastRegressModelWrapper",
    "SplitRegressModelWrapper",
]


def get_base_transform(imgsz: Union[int, tuple, list]):
    """
    根据给定的图像大小参数，返回一系列数据预处理变换。

    参数:
    imgsz (Union[int, tuple, list]): 图像大小参数。如果为整数，则图像将被调整为该大小的正方形；
                                     如果为元组或列表，则图像将被调整为指定的宽高比。

    返回:
    transforms.Compose: 包含图像大小调整和图像到张量转换的预处理步骤。
                        如果imgsz为None，则只返回图像到张量的转换。
    """
    # 检查imgsz是否提供了图像大小参数
    if imgsz:
        # 如果imgsz是整数，创建一个正方形尺寸的元组
        if isinstance(imgsz, int):
            imgsz = (imgsz, imgsz)
        # 返回一系列预处理变换，首先调整图像大小，然后将图像转换为张量
        return transforms.Compose([transforms.Resize(imgsz), transforms.ToTensor()])
    else:
        # 如果没有提供图像大小参数，仅返回将图像转换为张量的预处理步骤
        return transforms.ToTensor()


def get_train_transform(imgsz: Union[int, tuple, list]):
    """
    获取训练数据的转换器。

    如果提供了imgsz参数，根据其类型调整图像大小。总是应用一系列转换以增强训练数据的多样性。
    
    参数:
    imgsz (Union[int, tuple, list]): 图像大小。如果是整数，则将其转换为方形尺寸的元组。如果是元组或列表，则直接使用。

    返回:
    transforms.Compose: 一系列转换的组合。
    """
    if imgsz:
        # 如果imgsz是整数，将其转换为方形尺寸的元组
        if isinstance(imgsz, int):
            imgsz = (imgsz, imgsz)
        # 构建并返回一系列转换的组合，包括调整大小、颜色抖动、仿射变换、转换为张量和随机擦除
        return transforms.Compose(
            [
                transforms.Resize(imgsz),
                transforms.ColorJitter(
                    brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1
                ),  # 亮度、对比度、饱和度和色相
                transforms.RandomAffine(
                    degrees=(-10, 10),
                    translate=(0.1, 0.1),
                    scale=(0.9, 1.1),
                    shear=(-10, 10),
                ),
                transforms.ToTensor(),
                transforms.RandomErasing(
                    p=0.5, scale=(0.02, 0.33), ratio=(0.3, 3.3)
                ),  # 遮挡
            ]
        )
    else:
        # 如果没有提供imgsz参数，返回不包括调整大小的转换组合
        return transforms.Compose(
            [
                transforms.ColorJitter(
                    brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1
                ),  # 亮度、对比度、饱和度和色相
                transforms.RandomAffine(
                    degrees=(-10, 10),
                    translate=(0.1, 0.1),
                    scale=(0.9, 1.1),
                    shear=(-10, 10),
                ),
                transforms.ToTensor(),
                transforms.RandomErasing(
                    p=0.5, scale=(0.02, 0.33), ratio=(0.3, 3.3)
                ),  # 遮挡
            ]
        )
        return transforms.Compose(
            [
                transforms.ColorJitter(
                    brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1
                ),  # 亮度、对比度、饱和度和色相
                transforms.RandomAffine(
                    degrees=(-10, 10),
                    translate=(0.1, 0.1),
                    scale=(0.9, 1.1),
                    shear=(-10, 10),
                ),
                transforms.ToTensor(),
                transforms.RandomErasing(
                    p=0.5, scale=(0.02, 0.33), ratio=(0.3, 3.3)
                ),  # 遮挡
            ]
        )


class ImageClassifyModelWrapper(ClassifyModelWrapper):
    """
    根文件下包含train(必须)，test(可选), val(可选)文件夹

    Examples
    --------
    >>> model_wrapper = ImageClassifyModelWrapper(model, classes=classes)
    >>> model_wrapper.train(train_texts, y_train val_data, collate_fn)
    >>> model_wrapper.predict(test_texts)
    >>> model_wrapper.evaluate(test_texts, y_test)
    0.9876
    """

    test_dir: Optional[Path]

    def __init__(
        self,
        model_or_path: Union[nn.Module, str, Path],
        classes: Optional[Collection[str]] = None,
        device: Union[str, int, torch.device] = "auto",
    ):
        super().__init__(model_or_path, classes, device)
        self.test_dir = None
        self.imgsz = None
        self.transform = None

    def train(
        self,
        data: Union[str, Path],
        imgsz: Optional[Union[int, tuple, list]] = None,
        transform=None,
        train_transform=None,
        epochs: int = 100,
        optimizer: Optional[Union[type, optim.Optimizer]] = None,
        scheduler: Optional[LRScheduler] = None,
        lr: float = 0.001,
        T_max: int = 0,
        batch_size: int = 64,
        eval_batch_size: int = 128,
        sampler: Optional[Union[Sampler, bool]] = None,
        weight: Optional[Union[torch.Tensor, np.ndarray, List]] = None,
        num_workers: int = 0,
        num_eval_workers: int = 0,
        pin_memory: bool = False,
        pin_memory_device: str = "",
        persistent_workers: bool = False,
        early_stopping_rounds: Optional[int] = None,
        print_per_rounds: int = 1,
        drop_last: bool = False,
        checkpoint_per_rounds: int = 0,
        checkpoint_name="model.pt",
        show_progress=True,
        amp: bool = False,
        amp_dtype: Optional[torch.dtype] = None,
        eps=1e-5,
        monitor: ClassifyMonitor = "accuracy"
    ) -> dict:
        """
        训练模型的主函数，支持多种数据集目录结构和训练配置。

        参数:
            data (Union[str, Path]): 数据集的根目录路径，可以是字符串或Path对象。
            imgsz (Union[int, tuple, list], optional): 输入图像的尺寸，默认为None。
            transform (optional): 数据预处理的通用变换，默认为None。
            train_transform (optional): 训练集专用的预处理变换，默认为None。
            epochs (int, optional): 训练的总轮数，默认为100。
            optimizer (Union[type, optim.Optimizer], optional): 优化器类型或实例，默认为None。
            scheduler (LRScheduler, optional): 学习率调度器，默认为None。
            lr (float, optional): 初始学习率，默认为0.001。
            T_max (int, optional): 学习率调度器的最大迭代次数，默认为0。
            batch_size (int, optional): 训练时的批量大小，默认为64。
            eval_batch_size (int, optional): 验证或测试时的批量大小，默认为128。
            sampler (Union[Sampler, bool], optional): 数据采样器，布尔值表示是否启用平衡采样，默认为None。
            weight (Union[torch.Tensor, np.ndarray, List], optional): 类别权重，用于平衡采样，默认为None。
            num_workers (int, optional): 数据加载的线程数，默认为0。
            num_eval_workers (int, optional): 验证或测试时的数据加载线程数，默认为0。
            pin_memory (bool, optional): 是否将数据加载到CUDA的固定内存中，默认为False。
            pin_memory_device (str, optional): 固定内存的设备名称，默认为空字符串。
            persistent_workers (bool, optional): 是否保持数据加载线程持久化，默认为False。
            early_stopping_rounds (int, optional): 提前停止的轮数，默认为None。
            print_per_rounds (int, optional): 每隔多少轮打印一次训练信息，默认为1。
            drop_last (bool, optional): 是否丢弃最后一个不完整的批次，默认为False。
            checkpoint_per_rounds (int, optional): 每隔多少轮保存一次检查点，默认为0。
            checkpoint_name (str, optional): 检查点文件的名称，默认为"model.pt"。
            show_progress (bool, optional): 是否显示训练进度条，默认为True。
            amp (bool): 是否启用自动混合精度训练，默认为False。RNN模型在CPU上不支持自动混合精度训练。
            amp_dtype (torch.dtype): 自动混合精度训练的精度类型，默认为None。
            eps (float, optional): 数值稳定性的极小值，默认为1e-5。
            monitor (str, optional): 监控指标的名称，默认为"accuracy"。

        返回:
            dict: 包含训练结果的字典，通常包括损失、准确率等指标。
        """
        if isinstance(data, str):
            data = Path(data)

        assert data.exists(), f"Data directory {data} does not exist"

        train_dir = data / "train"
        test_dir = data / "test"
        val_dir = data / "val"
        if not val_dir.exists():
            val_dir = data / "valid"

        assert train_dir.exists(), f"Train directory {train_dir} does not exist"
        train_transform = train_transform or transform or get_train_transform(imgsz)
        self.transform = transform or get_base_transform(imgsz)
        train_set = ImageFolder(str(train_dir), train_transform)
        self.classes = train_set.classes
        if sampler is not None and isinstance(sampler, bool):
            if sampler:
                if weight is None:
                    sampler, weight = self.get_balance_sampler(np.array(train_set.targets), return_weights=True)
                else:
                    sampler = self.get_balance_sampler_from_weights(np.array(train_set.targets), weight)
            else:
                sampler = None
        log_utils.info(f"Classes: {self.classes}")

        if val_dir.exists():
            val_set = ImageFolder(str(val_dir), self.transform)
            result = super().train(
                train_set,
                val_set,
                epochs=epochs,
                optimizer=optimizer,
                scheduler=scheduler,
                lr=lr,
                T_max=T_max,
                batch_size=batch_size,
                eval_batch_size=eval_batch_size,
                sampler=sampler,
                weight=weight,
                num_workers=num_workers,
                num_eval_workers=num_eval_workers,
                pin_memory=pin_memory,
                pin_memory_device=pin_memory_device,
                persistent_workers=persistent_workers,
                early_stopping_rounds=early_stopping_rounds,
                print_per_rounds=print_per_rounds,
                drop_last=drop_last,
                checkpoint_per_rounds=checkpoint_per_rounds,
                checkpoint_name=checkpoint_name,
                show_progress=show_progress,
                amp=amp,
                amp_dtype=amp_dtype,
                eps=eps,
                monitor=monitor,
            )
            if test_dir.exists():
                self.test_dir = test_dir
                test_set = ImageFolder(str(val_dir), self.transform)
                preds, targets = acc_predict_dataset(self.best_model, test_set, eval_batch_size, 0.5, num_eval_workers, None, self.device)
                preds, targets = preds.ravel(), targets.ravel()
                metrics = self._cal_metrics(preds, targets, len(self.classes))
                self._print_metrics(metrics, targets, preds, "Test")
            else:
                preds, targets = acc_predict_dataset(self.best_model, val_set, eval_batch_size, 0.5, num_eval_workers, None, self.device)
                preds, targets = preds.ravel(), targets.ravel()
                metrics = self._cal_metrics(preds, targets, len(self.classes))
                self._print_metrics(metrics, targets, preds, "Valid")
            return result
        elif test_dir.exists():
            self.test_dir = test_dir
            test_set = ImageFolder(str(test_dir), self.transform)
            result = super().train(
                train_set,
                test_set,
                epochs=epochs,
                optimizer=optimizer,
                scheduler=scheduler,
                lr=lr,
                T_max=T_max,
                batch_size=batch_size,
                eval_batch_size=eval_batch_size,
                sampler=sampler,
                weight=weight,
                num_workers=num_workers,
                num_eval_workers=num_eval_workers,
                pin_memory=pin_memory,
                pin_memory_device=pin_memory_device,
                persistent_workers=persistent_workers,
                early_stopping_rounds=early_stopping_rounds,
                print_per_rounds=print_per_rounds,
                drop_last=drop_last,
                checkpoint_per_rounds=checkpoint_per_rounds,
                checkpoint_name=checkpoint_name,
                show_progress=show_progress,
                amp=amp,
                amp_dtype=amp_dtype,
                eps=eps,
                monitor=monitor,
            )
            preds, targets = acc_predict_dataset(self.best_model, test_set, eval_batch_size, 0.5, num_eval_workers, None, self.device)
            preds, targets = preds.ravel(), targets.ravel()
            metrics = self._cal_metrics(preds, targets, len(self.classes))
            self._print_metrics(metrics, targets, preds, "Test")
            return result
        
        return super().train(
            train_set,
            epochs=epochs,
            optimizer=optimizer,
            scheduler=scheduler,
            lr=lr,
            T_max=T_max,
            batch_size=batch_size,
            sampler=sampler,
            weight=weight,
            num_workers=num_workers,
            pin_memory=pin_memory,
            pin_memory_device=pin_memory_device,
            persistent_workers=persistent_workers,
            early_stopping_rounds=early_stopping_rounds,
            print_per_rounds=print_per_rounds,
            drop_last=drop_last,
            checkpoint_per_rounds=checkpoint_per_rounds,
            checkpoint_name=checkpoint_name,
            show_progress=show_progress,
            amp=amp,
            amp_dtype=amp_dtype,
            eps=eps,
            monitor=monitor,
        )
    
    def train_evaluate(
        self,
        data: Union[str, Path],
        imgsz: Optional[Union[int, tuple, list]] = None,
        transform=None,
        train_transform=None,
        epochs: int = 100,
        optimizer: Optional[Union[type, optim.Optimizer]] = None,
        scheduler: Optional[LRScheduler] = None,
        lr: float = 0.001,
        T_max: int = 0,
        batch_size: int = 64,
        eval_batch_size: int = 128,
        sampler: Optional[Union[Sampler, bool]] = None,
        weight: Optional[Union[torch.Tensor, np.ndarray, List]] = None,
        num_workers: int = 0,
        num_eval_workers: int = 0,
        pin_memory: bool = False,
        pin_memory_device: str = "",
        persistent_workers: bool = False,
        early_stopping_rounds: Optional[int] = None,
        print_per_rounds: int = 1,
        drop_last: bool = False,
        checkpoint_per_rounds: int = 0,
        checkpoint_name="model.pt",
        show_progress=True,
        amp: bool = False,
        amp_dtype: Optional[torch.dtype] = None,
        eps=1e-5,
        monitor: ClassifyMonitor = "accuracy"
    ) -> dict:
        """
        训练模型的主函数，支持多种数据集目录结构和训练配置。

        参数:
            data (Union[str, Path]): 数据集的根目录路径，可以是字符串或Path对象。
            imgsz (Union[int, tuple, list], optional): 输入图像的尺寸，默认为None。
            transform (optional): 数据预处理的通用变换，默认为None。
            train_transform (optional): 训练集专用的预处理变换，默认为None。
            epochs (int, optional): 训练的总轮数，默认为100。
            optimizer (Union[type, optim.Optimizer], optional): 优化器类型或实例，默认为None。
            scheduler (LRScheduler, optional): 学习率调度器，默认为None。
            lr (float, optional): 初始学习率，默认为0.001。
            T_max (int, optional): 学习率调度器的最大迭代次数，默认为0。
            batch_size (int, optional): 训练时的批量大小，默认为64。
            eval_batch_size (int, optional): 验证或测试时的批量大小，默认为128。
            sampler (Union[Sampler, bool], optional): 数据采样器，布尔值表示是否启用平衡采样，默认为None。
            weight (Union[torch.Tensor, np.ndarray, List], optional): 类别权重，用于平衡采样，默认为None。
            num_workers (int, optional): 数据加载的线程数，默认为0。
            num_eval_workers (int, optional): 验证或测试时的数据加载线程数，默认为0。
            pin_memory (bool, optional): 是否将数据加载到CUDA的固定内存中，默认为False。
            pin_memory_device (str, optional): 固定内存的设备名称，默认为空字符串。
            persistent_workers (bool, optional): 是否保持数据加载线程持久化，默认为False。
            early_stopping_rounds (int, optional): 提前停止的轮数，默认为None。
            print_per_rounds (int, optional): 每隔多少轮打印一次训练信息，默认为1。
            drop_last (bool, optional): 是否丢弃最后一个不完整的批次，默认为False。
            checkpoint_per_rounds (int, optional): 每隔多少轮保存一次检查点，默认为0。
            checkpoint_name (str, optional): 检查点文件的名称，默认为"model.pt"。
            show_progress (bool, optional): 是否显示训练进度条，默认为True。
            amp (bool): 是否启用自动混合精度训练，默认为False。RNN模型在CPU上不支持自动混合精度训练。
            amp_dtype (torch.dtype): 自动混合精度训练的精度类型，默认为None。
            eps (float, optional): 数值稳定性的极小值，默认为1e-5。
            monitor (str, optional): 监控指标的名称，默认为"accuracy"。

        返回:
            dict: 包含训练结果的字典，通常包括损失、准确率等指标。
        """
        if isinstance(data, str):
            data = Path(data)

        test_dir = data / "test"
        val_dir = data / "val"
        assert test_dir.exists() or val_dir.exists() or (data / "valid").exists()
        return self.train(data, imgsz, transform, train_transform, epochs, optimizer, scheduler, lr, T_max,
                          batch_size, eval_batch_size, sampler, weight, num_workers, num_eval_workers, pin_memory, pin_memory_device, 
                          persistent_workers, early_stopping_rounds, print_per_rounds, drop_last,
                          checkpoint_per_rounds, checkpoint_name, show_progress, amp, amp_dtype, eps, monitor)

    def predict(
        self,
        source: Union[str, Path, Image.Image, list, tuple, np.ndarray, torch.Tensor],
        imgsz: Optional[Union[int, tuple, list]] = None,
        batch_size: int = 64,
    ) -> np.ndarray:
        """
        :param source:
        :param imgsz: 图片大小
        """
        logits = self.logits(source, imgsz, batch_size)
        return acc_predict(logits.cpu())

    def predict_classes(
        self,
        source: Union[str, Path, Image.Image, list, tuple, np.ndarray, torch.Tensor],
        imgsz: Optional[Union[int, tuple, list]] = None,
        batch_size: int = 64,
    ) -> list:
        """
        :param source:
        :param imgsz: 图片大小
        """
        pred = self.predict(source, imgsz, batch_size)
        return self._predict_classes(pred.ravel())

    def predict_proba(
        self,
        source: Union[str, Path, Image.Image, list, tuple, np.ndarray, torch.Tensor],
        imgsz: Optional[Union[int, tuple, list]] = None,
        batch_size: int = 64,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        :param source:
        :param imgsz: 图片大小
        """
        logits = self.logits(source, imgsz, batch_size)
        return self._proba(logits)

    def predict_classes_proba(
        self,
        source: Union[str, Path, Image.Image, list, tuple, np.ndarray, torch.Tensor],
        imgsz: Optional[Union[int, tuple, list]] = None,
        batch_size: int = 64,
    ) -> Tuple[list, np.ndarray]:
        """
        :param source:
        :param imgsz: 图片大小
        """
        indices, values = self.predict_proba(source, imgsz, batch_size)
        return self._predict_classes(indices.ravel()), values

    def logits(
        self,
        source: Union[str, Path, Image.Image, list, tuple, np.ndarray, torch.Tensor],
        imgsz: Optional[Union[int, tuple, list]] = None,
        batch_size: int = 64,
    ) -> torch.Tensor:
        """
        计算输入图像的logits（未归一化的预测值）。

        参数:
        - source (Union[str, Path, Image.Image, list, tuple, np.ndarray, torch.Tensor]): 
          输入数据源，可以是文件路径、PIL图像对象、图像目录、NumPy数组或PyTorch张量。
        - imgsz (Union[int, tuple, list], 可选): 
          图像的尺寸，用于调整输入图像大小。如果未提供，则使用self.imgsz。
        - batch_size (int, 可选): 
          批处理大小，默认为64。

        返回:
        - torch.Tensor: 
          输入图像的logits（未归一化的预测值）。
        """
        
        # 如果未提供imgsz，则使用默认的self.imgsz
        imgsz = imgsz or self.imgsz 

        # 根据是否提供imgsz来定义图像预处理的变换
        if imgsz:
            transform = transforms.Compose(
                [transforms.Resize(imgsz), transforms.ToTensor()]
            )
        else:
            if self.transform:
                transform = self.transform
            else:
                raise ValueError("Expected 'imgsz', but None")

        # 如果source是字符串路径，转换为Path对象
        if isinstance(source, str):
            source = Path(source)

        # 如果source是Path对象，判断其是文件还是目录
        if isinstance(source, Path):
            if source.is_file():
                # 如果是文件，直接加载图像
                source = Image.open(source)
            elif source.is_dir():
                # 如果是目录，遍历目录中的所有图像文件
                source = (
                    img
                    for img in source.rglob("*")
                    if img.suffix in (".png", ".jpg", "jpeg") and img.is_file()
                )
                # 对每个图像文件进行预处理并堆叠成一个批次
                source = [transform(Image.open(s)).unsqueeze(0) for s in source]
                source = torch.cat(source, dim=0)

        # 如果source是PIL图像对象，进行预处理并添加批次维度
        if isinstance(source, Image.Image):
            source = transform(source)
            source = source.unsqueeze(0)

        return super().logits(source, batch_size)

    def acc(
        self,
        data: Optional[Union[str, Path, Dataset]] = None,
        imgsz: Optional[Union[int, tuple, list]] = None,
        transform=None,
        batch_size: int = 64,
        num_workers: int = 0,
    ) -> float:
        """return accuracy"""
        dataset = self._to_dataset(data, imgsz, transform)
        return super().acc(dataset, batch_size, num_workers)
    
    def confusion_matrix(
        self,
        data: Optional[Union[str, Path, Dataset]] = None,
        imgsz: Optional[Union[int, tuple, list]] = None,
        transform=None,
        batch_size: int = 64,
        num_workers: int = 0,
        verbose: bool = True,
    ) -> float:
        """return confusion matrix"""
        dataset = self._to_dataset(data, imgsz, transform)
        return super().confusion_matrix(dataset, batch_size, num_workers, verbose=verbose)

    def evaluate(
        self,
        data: Optional[Union[str, Path, Dataset]] = None,
        imgsz: Optional[Union[int, tuple, list]] = None,
        transform=None,
        batch_size: int = 64,
        num_workers: int = 0,
        verbose: bool = True,
    ) -> float:
        """return metrics"""
        dataset = self._to_dataset(data, imgsz, transform)
        return super().evaluate(dataset, batch_size, num_workers, verbose=verbose)     
    
    def classification_report(
        self,
        data: Union[str, Path, Dataset] = None,
        imgsz: Union[int, tuple, list] = None,
        transform=None,
        batch_size: int = 64,
        num_workers: int = 0,
        target_names: Optional[List] = None,
        verbose: bool = True,
    ) -> Union[str, dict]:
        dataset = self._to_dataset(data, imgsz, transform)
        return super().classification_report(dataset, batch_size, num_workers, target_names=target_names, verbose=verbose)
        
    def _to_dataset(
        self,
        data: Optional[Union[str, Path, Dataset]] = None,
        imgsz: Optional[Union[int, tuple, list]] = None,
        transform=None,
    ) -> Dataset:
        data = data or self.test_dir
        if isinstance(data, (str, Path)):
            transform = transform or get_base_transform(imgsz)
            return ImageFolder(data, transform)
        elif isinstance(data, ImageFolder):
            data.transform = data.transform or get_base_transform(imgsz)

        return data

    def _print_metrics(self, metrics: dict, labels: np.ndarray, preds: np.ndarray, dataset_type: str) -> None:
        print()
        print("==", f"{dataset_type} Dataset Metrics", "==")
        print(f"Accuracy: {metrics['accuracy']:.2%}")
        print(f"Precision: {metrics['precision']:.2%}")
        print(f"Recall: {metrics['recall']:.2%}")
        print(f"F1: {metrics['f1']:.2%}")
        print(f"AUC: {metrics['auc']:.2%}\n")

        self._print_classification_report(classification_report(labels, preds, target_names=self.classes))
        

class SplitImageClassifyModelWrapper(ImageClassifyModelWrapper):
    """
    根文件下是分类文件夹

    Examples
    --------
    >>> model_wrapper = SplitImageClassifyModelWrapper(model, classes=classes)
    >>> model_wrapper.train(train_texts, y_train val_data, collate_fn)
    >>> model_wrapper.predict(test_texts)
    >>> model_wrapper.evaluate(test_texts, y_test)
    0.9876
    """

    def __init__(
        self,
        model_or_path: Union[nn.Module, str, Path],
        classes: Optional[Collection[str]] = None,
        device: Union[str, int, torch.device] = "auto",
    ):
        super().__init__(model_or_path, classes, device)

    def train(
        self,
        data: Union[str, Path, ImageFolder],
        val_size=0.2,
        random_state: Optional[int] = None,
        imgsz: Optional[Union[int, tuple, list]] = None,
        transform=None,
        train_transform=None,
        epochs: int = 100,
        optimizer: Optional[Union[type, optim.Optimizer]] = None,
        scheduler: Optional[LRScheduler] = None,
        lr: float = 0.001,
        T_max: int = 0,
        batch_size: int = 64,
        eval_batch_size: int = 128,
        sampler: Optional[Union[Sampler, bool]] = None,
        weight: Optional[Union[torch.Tensor, np.ndarray, List]] = None,
        num_workers: int = 0,
        num_eval_workers: int = 0,
        pin_memory: bool = False,
        pin_memory_device: str = "",
        persistent_workers: bool = False,
        early_stopping_rounds: Optional[int] = None,
        print_per_rounds: int = 1,
        drop_last: bool = False,
        checkpoint_per_rounds: int = 0,
        checkpoint_name="model.pt",
        show_progress=True,
        amp: bool = False,
        amp_dtype: Optional[torch.dtype] = None,
        eps=1e-5,
        monitor: ClassifyMonitor = "accuracy"
    ) -> dict:
        """
        训练图像分类模型的函数。

        参数:
            data (Union[str, Path, ImageFolder]): 训练数据集，可以是路径、Path对象或ImageFolder对象。
            val_size (float): 验证集占总数据集的比例，默认为0.2。
            random_state (int): 随机种子，用于数据集划分，默认为None。
            imgsz (Union[int, tuple, list]): 输入图像的尺寸，默认为None。
            transform: 数据预处理的通用变换，默认为None。
            train_transform: 仅用于训练集的特定变换，默认为None。
            epochs (int): 训练的总轮数，默认为100。
            optimizer (Union[type, optim.Optimizer]): 优化器类型或实例，默认为None。
            scheduler (LRScheduler): 学习率调度器，默认为None。
            lr (float): 初始学习率，默认为0.001。
            T_max (int): 学习率调度器的最大迭代次数，默认为0。
            batch_size (int): 训练时的批量大小，默认为64。
            eval_batch_size (int): 验证时的批量大小，默认为128。
            sampler (Union[Sampler, bool]): 数据采样器，默认为None。
            weight (Union[torch.Tensor, np.ndarray, List]): 损失函数的权重，默认为None。
            num_workers (int): 数据加载的子进程数，默认为0。
            num_eval_workers (int): 验证数据加载的子进程数，默认为0。
            pin_memory (bool): 是否将数据加载到CUDA的固定内存中，默认为False。
            pin_memory_device (str): 固定内存设备的名称，默认为空字符串。
            persistent_workers (bool): 是否保持数据加载的子进程运行，默认为False。
            early_stopping_rounds (int): 提前停止的轮数，默认为None。
            print_per_rounds (int): 打印训练信息的间隔轮数，默认为1。
            drop_last (bool): 是否丢弃最后一个不完整的批次，默认为False。
            checkpoint_per_rounds (int): 保存检查点的间隔轮数，默认为0。
            checkpoint_name (str): 检查点文件的名称，默认为"model.pt"。
            show_progress (bool): 是否显示训练进度条，默认为True。
            amp (bool): 是否启用自动混合精度训练，默认为False。RNN模型在CPU上不支持自动混合精度训练。
            amp_dtype (torch.dtype): 自动混合精度训练的精度类型，默认为None。
            eps (float): 数值稳定性的极小值，默认为1e-5。
            monitor (str): 监控指标的名称，默认为"accuracy"。

        返回:
            dict: 包含训练结果的字典，通常包括最佳模型的状态和性能指标。
        """
        train_set, val_set = self._before(data, val_size, random_state, imgsz, transform, train_transform)

        # 调用的是ImageClassifyModelWrapper父类ClassifyModelWrapper的train方法
        return super(ImageClassifyModelWrapper, self).train(
            train_set,
            val_set,
            epochs=epochs,
            optimizer=optimizer,
            scheduler=scheduler,
            lr=lr,
            T_max=T_max,
            batch_size=batch_size,
            eval_batch_size=eval_batch_size,
            sampler=sampler,
            weight=weight,
            num_workers=num_workers,
            num_eval_workers=num_eval_workers,
            pin_memory=pin_memory,
            pin_memory_device=pin_memory_device,
            persistent_workers=persistent_workers,
            early_stopping_rounds=early_stopping_rounds,
            print_per_rounds=print_per_rounds,
            drop_last=drop_last,
            checkpoint_per_rounds=checkpoint_per_rounds,
            checkpoint_name=checkpoint_name,
            show_progress=show_progress,
            amp=amp,
            amp_dtype=amp_dtype,
            eps=eps,
            monitor=monitor
        )
    
    def train_evaluate(
        self,
        data: Union[str, Path, ImageFolder],
        val_size=0.2,
        random_state: Optional[int] = None,
        imgsz: Optional[Union[int, tuple, list]] = None,
        transform=None,
        train_transform=None,
        epochs: int = 100,
        optimizer: Optional[Union[type, optim.Optimizer]] = None,
        scheduler: Optional[LRScheduler] = None,
        lr: float = 0.001,
        T_max: int = 0,
        batch_size: int = 64,
        eval_batch_size: int = 128,
        sampler: Optional[Sampler] = None,
        weight: Optional[Union[torch.Tensor, np.ndarray, List]] = None,
        num_workers: int = 0,
        num_eval_workers: int = 0,
        pin_memory: bool = False,
        pin_memory_device: str = "",
        persistent_workers: bool = False,
        early_stopping_rounds: Optional[int] = None,
        print_per_rounds: int = 1,
        drop_last: bool = False,
        checkpoint_per_rounds: int = 0,
        checkpoint_name="model.pt",
        show_progress=True,
        amp: bool = False,
        amp_dtype: Optional[torch.dtype] = None,
        eps=1e-5,
        monitor: ClassifyMonitor = "accuracy",
        verbose: bool = True,
        threshold: float = 0.5,
        target_names: Optional[List[str]] = None,
        num_classes: Optional[int] = None
    ) -> Tuple[dict, dict]:
        """
        训练并评估分类模型。

        参数:
            data (Union[str, Path, ImageFolder]): 数据集路径或ImageFolder对象。
            val_size (float): 验证集占总数据集的比例，默认为0.2。
            random_state (int): 随机种子，用于划分训练集和验证集。
            imgsz (Union[int, tuple, list]): 输入图像的尺寸，默认为None。
            transform: 数据预处理变换，默认为None。
            train_transform: 仅用于训练集的数据增强变换，默认为None。
            epochs (int): 训练的总轮数，默认为100。
            optimizer (Union[type, optim.Optimizer]): 优化器类型或实例，默认为None。
            scheduler (LRScheduler): 学习率调度器，默认为None。
            lr (float): 初始学习率，默认为0.001。
            T_max (int): 学习率调度器的周期长度，默认为0。
            batch_size (int): 训练时的批量大小，默认为64。
            eval_batch_size (int): 验证时的批量大小，默认为128。
            sampler (Sampler): 数据采样器，默认为None。
            weight (Union[torch.Tensor, np.ndarray, List]): 类别权重，默认为None。
            num_workers (int): 数据加载的子进程数，默认为0。
            num_eval_workers (int): 验证数据加载的子进程数，默认为0。
            pin_memory (bool): 是否将数据加载到CUDA固定内存中，默认为False。
            pin_memory_device (str): 固定内存设备的名称，默认为空字符串。
            persistent_workers (bool): 是否保持数据加载的子进程运行，默认为False。
            early_stopping_rounds (int): 提前停止的轮数阈值，默认为None。
            print_per_rounds (int): 每隔多少轮打印一次日志，默认为1。
            drop_last (bool): 是否丢弃最后一个不完整的批次，默认为False。
            checkpoint_per_rounds (int): 每隔多少轮保存一次检查点，默认为0。
            checkpoint_name (str): 检查点文件名，默认为"model.pt"。
            show_progress (bool): 是否显示进度条，默认为True。
            amp (bool): 是否启用自动混合精度训练，默认为False。RNN模型在CPU上不支持自动混合精度训练。
            amp_dtype (torch.dtype): 自动混合精度训练的精度类型，默认为None。
            eps (float): 数值稳定性的极小值，默认为1e-5。
            monitor (str): 监控指标（如"accuracy"），用于提前停止或保存最佳模型。
            verbose (bool): 是否输出详细信息，默认为True。
            threshold (float): 分类阈值，默认为0.5。
            target_names (List[str]): 类别标签名称列表，默认为None。
            num_classes (int): 类别数量，默认为None。

        返回:
            Tuple[dict, dict]: 包含训练和验证结果的字典。
        """
        train_set, val_set = self._before(data, val_size, random_state, imgsz, transform, train_transform)

        # 调用的是ImageClassifyModelWrapper父类ClassifyModelWrapper的train_evaluate方法
        return super(ImageClassifyModelWrapper, self).train_evaluate(
            train_set,
            val_set,
            epochs=epochs,
            optimizer=optimizer,
            scheduler=scheduler,
            lr=lr,
            T_max=T_max,
            batch_size=batch_size,
            eval_batch_size=eval_batch_size,
            sampler=sampler,
            weight=weight,
            num_workers=num_workers,
            num_eval_workers=num_eval_workers,
            pin_memory=pin_memory,
            pin_memory_device=pin_memory_device,
            persistent_workers=persistent_workers,
            early_stopping_rounds=early_stopping_rounds,
            print_per_rounds=print_per_rounds,
            drop_last=drop_last,
            checkpoint_per_rounds=checkpoint_per_rounds,
            checkpoint_name=checkpoint_name,
            show_progress=show_progress,
            amp=amp,
            amp_dtype=amp_dtype,
            eps=eps,
            monitor=monitor,
            verbose=verbose,
            threshold=threshold,
            target_names=target_names,
            num_classes=num_classes
        )

    def _before(self, data, val_size: float, random_state, imgsz, transform, train_transform):
        """
        准备训练集和验证集的预处理逻辑。

        参数:
            data (str, Path, ImageFolder): 数据源，可以是数据目录路径（str 或 Path）或 ImageFolder 对象。
            val_size (float): 验证集占总数据集的比例，范围为 [0.0, 1.0)。
            random_state (int, optional): 随机数种子，用于确保数据划分的可重复性。如果为 None，则不固定随机性。
            imgsz (int): 图像的目标尺寸，用于生成默认的图像变换。
            transform (callable, optional): 自定义的图像变换，应用于验证集。
            train_transform (callable, optional): 自定义的图像变换，应用于训练集。

        返回:
            tuple: 包含两个元素：
                - train_set (Dataset): 训练集。
                - val_set (Dataset, optional): 验证集。如果 val_size 为 0.0，则返回 None。
        """
        # 确保验证集比例在有效范围内
        assert 0.0 <= val_size < 1.0

        if val_size > 0.0:
            # 如果未提供训练集变换，则使用默认的训练集变换
            train_transform = train_transform or transform or get_train_transform(imgsz)

            if isinstance(data, (str, Path)):
                # 如果数据源是路径，则加载 ImageFolder 数据集
                dataset = ImageFolder(root=data)
                self.transform = transform or get_base_transform(imgsz)
            elif isinstance(data, ImageFolder):
                # 如果数据源是 ImageFolder 对象，则直接使用
                dataset = data
                self.transform = (
                    transform or dataset.transform or get_train_transform(imgsz)
                )
            else:
                # 如果数据源类型不支持，则抛出异常
                raise TypeError(
                    f"Expected str or Path or ImageFolder, but {type(data)}"
                )

            # 获取数据集的类别信息
            self.classes = dataset.classes

            # 根据验证集比例划分训练集和验证集
            train_size = 1 - val_size
            if random_state is None:
                train_set, val_set = random_split(dataset, [train_size, val_size])
            else:
                generator = torch.Generator().manual_seed(random_state)
                train_set, val_set = random_split(dataset, [train_size, val_size], generator)

            # 分别设置训练集和验证集的图像变换
            train_set.dataset.transform = train_transform
            val_set.dataset.transform = self.transform
        else:
            # 如果验证集比例为 0，则只生成训练集
            val_set = None
            if isinstance(data, (str, Path)):
                train_set = ImageFolder(root=data, transform=train_transform)
            elif isinstance(data, ImageFolder):
                train_set = data
                train_set.transform = (
                    train_transform
                    or train_set.transform
                    or transform
                    or get_train_transform(imgsz)
                )
            self.classes = train_set.classes

        # 打印类别信息
        log_utils.info(f"Classes: {self.classes}")

        return train_set, val_set

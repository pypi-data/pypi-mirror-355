import math
import torch
import random
import numpy as np
from torchvision import datasets, transforms
from torch.utils.data import Subset, Dataset, random_split

__all__ = ['Region', 'Environment', 'download_dataset', 'split_train_validation', 'partition_to_subregions']

class Region:

    def __init__(self, mid: int, training_data: Subset, validation_data: Subset):
        self.mid = mid
        self.training_data = training_data
        self.validation_data = validation_data


    def distribute_to_devices(self, number_of_devices: int) -> dict[int, tuple[Subset, Subset]]:
        device_to_subset = dict()
        training_dataset, training_indices = self.training_data.dataset, self.training_data.indices
        validation_dataset, validation_indices = self.validation_data.dataset, self.validation_data.indices
        training_split = np.array_split(training_indices, number_of_devices)
        validation_split = np.array_split(validation_indices, number_of_devices)
        for index, (training, validation) in enumerate(zip(training_split, validation_split)):
            device_to_subset[index] = (Subset(training_dataset, training), Subset(validation_dataset, validation))
        return device_to_subset


class Environment:

    def __init__(self, partitions: dict[int, tuple[Subset, Subset]]):
        self.regions = [Region(id, training_data, validation_data) for id, (training_data, validation_data) in partitions.items()]


    def from_subregion_to_devices(self, region_id: int, number_of_devices: int):
        return self.regions[region_id].distribute_to_devices(number_of_devices)


def download_dataset(dataset_name: str, transform: transforms.Compose = None, download_path: str = 'dataset') -> tuple[Dataset,Dataset]:
    """
    Download the specified dataset from torchvision.
    Valid datasets are: MNIST, FashionMNIST, Extended MNIST, CIFAR10, CIFAR100.
    :param dataset_name: The dataset to be downloaded.
    :param transform: Transformations that will be applied to the dataset. If none only ToTensor will be applied.
    :param download_path: The path where the dataset will be downloaded.
    :return: the specified dataset.
    """
    if transform is None:
        transform = transforms.Compose([transforms.ToTensor()])

    if dataset_name == 'MNIST':
        train_dataset = datasets.MNIST(root=download_path, train=True, download=True, transform=transform)
        test_dataset = datasets.MNIST(root=download_path, train=False, download=True, transform=transform)
    elif dataset_name == 'CIFAR10':
        train_dataset = datasets.CIFAR10(root=download_path, train=True, download=True, transform=transform)
        test_dataset = datasets.CIFAR10(root=download_path, train=False, download=True, transform=transform)
    elif dataset_name == 'CIFAR100':
        train_dataset = datasets.CIFAR100(root=download_path, train=True, download=True, transform=transform)
        test_dataset = datasets.CIFAR100(root=download_path, train=False, download=True, transform=transform)
    elif dataset_name == 'EMNIST':
        train_dataset = datasets.EMNIST(root=download_path, split='letters', train=True, download=True, transform=transform)
        test_dataset = datasets.EMNIST(root=download_path, split='letters', train=False, download=True, transform=transform)
    elif dataset_name == 'FashionMNIST':
        train_dataset = datasets.FashionMNIST(root=download_path, train=True, download=True, transform=transform)
        test_dataset = datasets.FashionMNIST(root=download_path, train=False, download=True, transform=transform)
    else:
        raise Exception(f'Dataset {dataset_name} not supported! Please check :)')
    return train_dataset, test_dataset


def split_train_validation(dataset: Dataset, train_validation_ratio: float) -> tuple[Subset, Subset]:
    """
    Split a given dataset in training and validation set.
    :param dataset: The dataset to be split in training and validation subsets.
    :param train_validation_ratio: The percentage of training instances, it must be a value between 0 and 1.
    :return: A tuple containing the training and validation subsets.
    """
    dataset_size = len(dataset)
    training_size = int(dataset_size * train_validation_ratio)
    validation_size = dataset_size - training_size
    training_data, validation_data = random_split(dataset, [training_size, validation_size])
    return training_data, validation_data


def partition_to_subregions(training_dataset, validation_dataset, partitioning_method: str, number_of_regions: int) -> Environment:
    """
    Splits a torch Subset following a given method.
    Implemented methods for label skewness are: IID, Hard, Dirichlet
    :param partitioning_method: a string containing the name of the partitioning method.
    :param dataset: a torch Subset containing the dataset to be partitioned.
    :param areas: the number of sub-areas.
    :return: a dict in which keys are the IDs of the subareas and the values are lists of IDs of the instances of the subarea
        (IDs references the original dataset).
    """
    if partitioning_method == 'Dirichlet':
        training_partitions = __partition_dirichlet(training_dataset, number_of_regions)
        validation_partitions = __partition_dirichlet(validation_dataset, number_of_regions)
    elif partitioning_method == 'Hard':
        training_partitions = __partition_hard(training_dataset, number_of_regions)
        validation_partitions = __partition_hard(validation_dataset, number_of_regions)
    elif partitioning_method == 'IID':
        training_partitions = __partition_iid(training_dataset, number_of_regions)
        validation_partitions = __partition_iid(validation_dataset, number_of_regions)
    else:
        raise Exception(f'Partitioning method {partitioning_method} not supported! Please check :)')

    partitions = dict()
    for k in training_partitions.keys():
        partitions[k] = (Subset(training_dataset, training_partitions[k]), Subset(validation_dataset, validation_partitions[k]))

    return Environment(partitions)


def __partition_hard(data, areas) -> dict[int, list[int]]:
    labels = len(data.dataset.classes)
    labels_set = np.arange(labels)
    split_classes_per_area = np.array_split(labels_set, areas)
    distribution = np.zeros((areas, labels))
    for i, elems in enumerate(split_classes_per_area):
        rows = [i for _ in elems]
        distribution[rows, elems] = 1 / len(elems)
    return __partition_by_distribution(distribution, data, areas)


def __partition_iid(data, areas) -> dict[int, list[int]]:
    labels = len(data.dataset.classes)
    percentage = 1 / labels
    distribution = np.zeros((areas, labels))
    distribution.fill(percentage)
    return __partition_by_distribution(distribution, data, areas)


def __partition_by_distribution(distribution: np.ndarray, data: Subset, areas: int) -> dict[int, list[int]]:
    indices = data.indices
    targets = data.dataset.targets
    class_counts = torch.bincount(targets[indices])
    class_to_indices = {}
    for index in indices:
        c = targets[index].item()
        if c in class_to_indices:
            class_to_indices[c].append(index)
        else:
            class_to_indices[c] = [index]
    max_examples_per_area = int(math.floor(len(indices) / areas))
    elements_per_class = torch.floor(torch.tensor(distribution) * max_examples_per_area).to(torch.int)
    partitions = {a: [] for a in range(areas)}
    for area in range(areas):
        elements_per_class_in_area = elements_per_class[area, :].tolist()
        for c in sorted(class_to_indices.keys()):
            elements = min(elements_per_class_in_area[c], class_counts[c].item())
            selected_indices = random.sample(class_to_indices[c], elements)
            partitions[area].extend(selected_indices)
    return partitions


def __partition_dirichlet(data, areas):
    # Implemented as in: https://proceedings.mlr.press/v97/yurochkin19a.html
    min_size = 0
    indices = data.indices
    targets = data.dataset.targets
    N = len(indices)
    class_to_indices = {}
    for index in indices:
        c = targets[index].item()
        if c in class_to_indices:
            class_to_indices[c].append(index)
        else:
            class_to_indices[c] = [index]
    partitions = {a: [] for a in range(areas)}
    while min_size < 10:
        idx_batch = [[] for _ in range(areas)]
        for k in sorted(class_to_indices.keys()):
            idx_k = class_to_indices[k]
            np.random.shuffle(idx_k)
            proportions = np.random.dirichlet(np.repeat(0.5, areas))
            ## Balance
            proportions = np.array([p * (len(idx_j) < N / areas) for p, idx_j in zip(proportions, idx_batch)])
            proportions = proportions / proportions.sum()
            proportions = (np.cumsum(proportions) * len(idx_k)).astype(int)[:-1]
            idx_batch = [idx_j + idx.tolist() for idx_j, idx in zip(idx_batch, np.split(idx_k, proportions))]
            min_size = min([len(idx_j) for idx_j in idx_batch])
    for j in range(areas):
        np.random.shuffle(idx_batch[j])
        partitions[j] = idx_batch[j]
    return partitions

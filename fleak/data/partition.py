import numpy as np

from .image_dataset import (
    load_mnist_dataset,
    load_cifar10_dataset,
    load_cifar100_dataset,
    load_tiny_imagenet_dataset
)


def iid_partition(dataset, n_parties):
    """
    :param dataset: torch dataset
    :param n_parties: number of parties
    :return: partitioned data index
    """
    data_idx = np.random.permutation(len(dataset))
    user_idx = np.array_split(data_idx, n_parties)
    return user_idx


def dirichlet_partition(dataset, n_parties, beta):
    """
    :param dataset: torch dataset
    :param n_parties: number of parties
    :param beta: parameter of Dirichlet distribution
    :return: partitioned data index
    """
    y_labels = np.array(dataset.targets)
    n_classes = len(set(y_labels))

    min_samples = 0
    min_required_samples = 15
    user_idx = []
    while min_samples < min_required_samples:
        user_idx = [[] for _ in range(n_parties)]
        for k in range(n_classes):
            data_idx_k = np.where(y_labels == k)[0]
            np.random.shuffle(data_idx_k)
            proportions = np.random.dirichlet(np.repeat(beta, n_parties))
            proportions = np.array([p * (len(idx) < len(dataset) / n_parties)
                                    for p, idx in zip(proportions, user_idx)])
            proportions = proportions / proportions.sum()
            # the rest of idx would be automatically allocated to the last party
            proportions = (np.cumsum(proportions) * len(data_idx_k)).astype(int)[:-1]
            user_idx = [uidx + idx.tolist() for uidx, idx in zip(user_idx, np.split(data_idx_k, proportions))]
            min_samples = min([len(idx) for idx in user_idx])
    for j in range(n_parties):
        np.random.shuffle(user_idx[j])
    return user_idx


def partition_dataset(dataset: str, data_dir: str, data_augment: bool, iid: bool, n_parties,
                      valid_prop=0, test_prop=0.2, beta=0.5, verbose=True):
    """
    Training part of the original dataset is allocated to multiple parties, each party manually
    divide the dataset into training / validation / testing data.
    Testing part of the original dataset is not partitioned
    :param dataset: name of the dataset
    :param data_dir: path of dataset
    :param data_augment: if using data augmentation
    :param iid: if using iid data
    :param n_parties: number of users
    :param valid_prop: proportion of validation data 0 <= v < 1
    :param test_prop: proportion of testing data 0 <= v < 1
    :param beta: hyperparameter of Dirichlet distribution
    :param verbose: if printing the partitioned client data labels
    :return: train_dataset, test_dataset, train_user_idx, valid_user_idx, test_user_idx
    """
    assert test_prop > 0
    if dataset == 'mnist':
        train_dataset, test_dataset = load_mnist_dataset(data_dir)
    elif dataset == 'cifar10':
        train_dataset, test_dataset = load_cifar10_dataset(data_dir, data_augment)
    elif dataset == 'cifar100':
        train_dataset, test_dataset = load_cifar100_dataset(data_dir, data_augment)
    elif dataset == 'tiny_imagenet':
        train_dataset, test_dataset = load_tiny_imagenet_dataset(data_dir)
    else:
        raise TypeError('{} is not an expected dataset !'.format(dataset))

    assert iid in [True, False]
    if iid:
        user_idx = iid_partition(train_dataset, n_parties)
    else:
        user_idx = dirichlet_partition(train_dataset, n_parties, beta)
    valid_user_idx = {i: user_idx[i][0:int(len(user_idx[i]) * valid_prop)] for i in range(n_parties)}
    test_user_idx = {i: user_idx[i][len(user_idx[i]) - int(len(user_idx[i]) * test_prop):] for i in range(n_parties)}
    train_user_idx = {
        i: user_idx[i][int(len(user_idx[i]) * valid_prop):len(user_idx[i]) - int(len(user_idx[i]) * test_prop)]
        for i in range(n_parties)}

    if verbose:
        train_user_label = {user: train_dataset.targets[idx] for (user, idx) in train_user_idx.items()}
        valid_user_label = {user: train_dataset.targets[idx] for (user, idx) in valid_user_idx.items()}
        test_user_label = {user: train_dataset.targets[idx] for (user, idx) in test_user_idx.items()}
        print('training labels: ', train_user_label)
        print('validation labels: ', valid_user_label)
        print('testing labels: ', test_user_label)

    return train_dataset, test_dataset, train_user_idx, valid_user_idx, test_user_idx

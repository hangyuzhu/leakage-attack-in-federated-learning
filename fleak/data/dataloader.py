from torch.utils.data import DataLoader

from .image_dataset import DatasetSplit
from .partition import partition_dataset


def generate_dataloaders(dataset: str, data_dir: str, data_augment: bool, iid: bool, n_parties,
                         valid_prop=0, test_prop=0.2, beta=0.5, batch_size=50, verbose=True):
    """
    Construct 3 dataloaders for clients and 1 test dataloader for the server
    This method is applicable for pfl approaches
    :param dataset: name of the dataset
    :param data_dir: path of dataset
    :param data_augment: if using data augmentation
    :param iid: if using iid data
    :param n_parties: number of users
    :param valid_prop: proportion of validation data 0 <= v < 1
    :param test_prop: proportion of testing data 0 <= v < 1
    :param beta: hyperparameter of Dirichlet distribution
    :param batch_size: training batch size
    :param verbose: if printing the partitioned client data labels
    :return: train_loaders, valid_loaders, test_loaders, test_loader (for server)
    """
    train_dataset, test_dataset, train_user_idx, valid_user_idx, test_user_idx = partition_dataset(
        dataset=dataset,
        data_dir=data_dir,
        data_augment=data_augment,
        iid=iid,
        n_parties=n_parties,
        valid_prop=valid_prop,
        test_prop=test_prop,
        beta=beta,
        verbose=verbose
    )

    # construct dataloaders
    train_loaders = [DataLoader(DatasetSplit(train_dataset, train_user_idx[i]), batch_size=batch_size, shuffle=True)
                     for i in range(n_parties)]
    valid_loaders = [DataLoader(DatasetSplit(train_dataset, valid_user_idx[i]), batch_size=batch_size)
                     for i in range(n_parties)]
    test_loaders = [DataLoader(DatasetSplit(train_dataset, test_user_idx[i]), batch_size=batch_size)
                     for i in range(n_parties)]
    test_loader = DataLoader(test_dataset, batch_size=batch_size)
    return train_loaders, valid_loaders, test_loaders, test_loader

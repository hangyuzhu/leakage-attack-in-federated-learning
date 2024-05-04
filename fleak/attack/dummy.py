import math
from typing import Union

import torch
import torch.nn as nn
from torchvision import transforms

from ..data.image_dataset import UnNormalize


class TorchDummy:
    """Base class for dummy data

    This module allows easy managing of dummy data
    Caution: dm & ds are not always available

    """

    def __init__(
        self,
        _input_shape: list,
        _label_shape: list,
        batch_size: int,
        dm: Union[list, tuple],
        ds: Union[list, tuple],
        device: str
    ):
        assert _input_shape[0] == batch_size
        assert _label_shape[0] == batch_size
        self.device = device
        self._input_shape = _input_shape
        self._label_shape = _label_shape
        self.batch_size = batch_size

        self.dm = dm
        self.ds = ds

        # buffer
        self.history = []
        self.labels = []

    @property
    def input_shape(self):
        return self._input_shape

    @property
    def label_shape(self):
        return self._label_shape

    def append(self, _dummy):
        self.history.append(_dummy)

    def append_label(self, _label):
        self.labels.append(_label)

    def clear_buffer(self):
        """ Clear the history buffer """
        self.history = []
        self.labels = []

    def generate_dummy_input(self, device=None):
        if device is None:
            device = self.device
        return torch.randn(self.input_shape).to(device).requires_grad_(True)

    def generate_dummy_label(self, device=None):
        if device is None:
            device = self.device
        return torch.randn(self.label_shape).to(device).requires_grad_(True)


class TorchDummyImage(TorchDummy):

    def __init__(
            self,
            image_shape: list,
            batch_size: int,
            n_classes: int,
            dm: Union[list, tuple],
            ds: Union[list, tuple],
            device: str
    ):
        """
        :param image_shape: 3D image shape
        :param batch_size: batch size
        :param n_classes: number of data classes
        :param dm: normalized mean value
        :param ds: normalized std value
        :param device: running device
        """
        # channel first image for pytorch
        assert len(image_shape) == 3
        # insert the batch dimension
        image_shape.insert(0, batch_size)

        self.n_classes = n_classes
        # label shape [N, C]
        label_shape = [batch_size, self.n_classes]
        super().__init__(
            _input_shape=image_shape,
            _label_shape=label_shape,
            batch_size=batch_size,
            dm=dm,
            ds=ds,
            device=device,
        )
        # inverse transform operator
        self._it = transforms.Compose([
            UnNormalize(dm, ds),
            transforms.ToPILImage()
        ])

        self.t_dm = torch.as_tensor(self.dm, device=device)[:, None, None]
        self.t_ds = torch.as_tensor(self.ds, device=device)[:, None, None]

    def append(self, _dummy):
        if len(_dummy) > 1:
            self.history.extend([self._it(x.cpu()) for x in _dummy])
        else:
            self.history.append(self._it(_dummy[0].cpu()))

    def append_label(self, _label):
        self.labels.extend([label.item() for label in _label])


def generate_dummy_k(dummy, device):
    """ Generate dummy data with Kaiming initialization

     This may be helpful for stable generation

    :param dummy: TorchDummy object
    :param device: cpu or cuda
    :return: dummy data & dummy label
     """
    dummy_data = torch.empty(dummy.input_shape).to(device).requires_grad_(True)
    # equivalent to the default initialization of pytorch
    nn.init.kaiming_uniform_(dummy_data, a=math.sqrt(5))
    dummy_label = torch.empty(dummy.label_shape).to(device).requires_grad_(True)
    nn.init.kaiming_uniform_(dummy_label, a=math.sqrt(5))
    return dummy_data, dummy_label


def generate_dummy(dummy, device):
    """ Generate dummy data with Gaussian distribution

    :param dummy: TorchDummy object
    :param device: cpu or cuda
    :return: dummy data & dummy label
    """
    dummy_data = torch.randn(dummy.input_shape).to(device).requires_grad_(True)
    dummy_label = torch.randn(dummy.label_shape).to(device).requires_grad_(True)
    return dummy_data, dummy_label

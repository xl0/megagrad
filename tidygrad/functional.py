# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/02_functional.ipynb.

# %% auto 0
__all__ = ['sigmoid', 'softmax', 'relu', 'BCE_loss', 'CrossEntropy_loss', 'dropout', 'Pad']

# %% ../nbs/02_functional.ipynb 2
import os

# os.environ["OMP_NUM_THREADS"] = "1"
# os.environ["OPENBLAS_NUM_THREADS"] = "1"
# os.environ["MKL_NUM_THREADS"] = "1"
# os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
# os.environ["NUMEXPR_NUM_THREADS"] = "1"

# MKL_NUM_THREADS=1
# NUMEXPR_NUM_THREADS=1
# OMP_NUM_THREADS=1

import numpy as np
from tidygrad.tensor import (
    Tensor,
    UnaryElementwiseOp,
    BinaryElementwiseOp,
    BaseOp,
    ExpLog,
)

# %% ../nbs/02_functional.ipynb 3
class Sigmoid(UnaryElementwiseOp):
    """Take the sigmoid of a tensor"""

    name_template = "sigmoid({})"

    def __init__(self, a, name=None):
        super().__init__(a, name=name)
        # self.out = Tensor(1 / (1 + np.exp(-self.args[0].data)), name=self.name, op=self)
        self.set_out(1 / (1 + np.exp(-self.args[0].data)))

    def backward(self):
        self.check_backward()
        with np.errstate(under="ignore"):  # Triggered by infinitesimally small 1-data
            self.parents[0].grad += self.out.grad * self.out.data * (1 - self.out.data)

# %% ../nbs/02_functional.ipynb 4
def sigmoid(input, name=None):
    return Sigmoid(input, name=name).out

# %% ../nbs/02_functional.ipynb 5
def softmax(input, name=None):
    exp = input.exp()
    return exp.div(exp.sum(axis=-1, keepdims=True), name=name)

# %% ../nbs/02_functional.ipynb 6
class Relu(UnaryElementwiseOp):
    """Take the sigmoid of a tensor"""

    name_template = "relu({})"

    def __init__(self, a, name=None):
        super().__init__(a, name=name)
        # self.out = Tensor(np.maximum(0, self.args[0].data), name=self.name, op=self)
        self.set_out(np.maximum(0, self.args[0].data))

    def backward(self):
        self.check_backward()
        self.parents[0].grad += self.out.grad * (self.out.data > 0)

# %% ../nbs/02_functional.ipynb 7
def relu(input, name=None):
    return Relu(input, name=name).out

# %% ../nbs/02_functional.ipynb 8
def BCE_loss(logits: Tensor, target: Tensor, reduction="mean"):
    loss = logits - logits * target + ExpLog(-logits).out
    if reduction == "mean":
        return loss.mean()
    if reduction == "sum":
        return loss.sum()
    assert 0, "Invalid reduction"

# %% ../nbs/02_functional.ipynb 9
def CrossEntropy_loss(logits: Tensor, target: Tensor, reduction="mean"):
    if not isinstance(target, Tensor):
        target = Tensor(target)
    sm = softmax(logits)
    loss = -target * sm.log()
    if reduction == "mean":
        return loss.mean()
    if reduction == "sum":
        return loss.sum()
    assert 0, "Invalid reduction"

# %% ../nbs/02_functional.ipynb 10
class Dropout(UnaryElementwiseOp):
    """Apply Dropout to a tensor"""

    name_template = "dropout({})"

    def __init__(self, a, p_drop=0.1, training=True, name=None):
        super().__init__(a, name=name)
        assert 0 < p_drop < 1, f"p_drop must in (0, 1), got {p_drop}"
        self.p_drop = p_drop
        self.training = training
        if training:
            # Note: We scale up the outputs during training rather than scaling down during inference.
            scale_factor = 1 / (1 - p_drop)
            self.mask = np.random.binomial(
                scale_factor, 1 - p_drop, size=self.args[0].data.shape
            )
            # self.out = Tensor(self.args[0].data * self.mask, name=self.name, op=self)
            self.set_out(self.args[0].data * self.mask)
        else:
            # self.out = Tensor(self.args[0].data, name=self.name, op=self)
            self.set_out(self.args[0].data)

    def backward(self):
        self.check_backward()
        self.parents[0].grad += self.out.grad * (self.mask if self.training else 1)

# %% ../nbs/02_functional.ipynb 11
class Embedding(UnaryElementwiseOp):
    """Embedding layer"""

    name_template = "embedding({})"

    def __init__(self, a, indices, name=None):
        super().__init__(a, name=name)
        self.indices = indices
        # self.out = Tensor(self.args[0].data[self.indices], name=self.name, op=self)
        self.set_out(self.args[0].data[self.indices])

    def backward(self):
        self.check_backward()
        self.parents[0].grad[self.indices] += self.out.grad

# %% ../nbs/02_functional.ipynb 12
def embedding(input, indices, name=None):
    return Embedding(input, indices, name=name).out

# %% ../nbs/02_functional.ipynb 13
def dropout(x, p=0.5, training=True):
    if p == 0:
        return x

    return Dropout(x, p_drop=p, training=training).out

# %% ../nbs/02_functional.ipynb 15
from typing import Union, Tuple

# %% ../nbs/02_functional.ipynb 18
class Pad(UnaryElementwiseOp):
    """Pad a tensor"""

    name_template = "pad2d({})"

    def __init__(self, a, padding: Union[int, Tuple[int, int]], name=None):
        super().__init__(a, name=name)
        self.padding = (padding, padding) if isinstance(padding, int) else padding
        self.out = Tensor(np_pad2d(a.data, self.padding), name=self.name, op=self)

    def backward(self):
        self.parents[0].grad += np_unpad2d(self.out.grad, self.padding)
        # pY, pX = self.padding
        # slices = (slice(None),) * (len(self.args[0].shape) - 2) \
        #     + (slice(pY, -pY),) + (slice(pX, -pX),)
        # self.parents[0].grad += self.out.grad[slices]

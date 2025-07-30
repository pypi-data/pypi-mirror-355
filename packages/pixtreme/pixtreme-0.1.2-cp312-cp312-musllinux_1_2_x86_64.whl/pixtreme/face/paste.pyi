from __future__ import annotations
import builtins as __builtins__
import cupy as cp
import numpy as np
from pixtreme.filter.gaussian import GaussianBlur
from pixtreme.transform.affine import affine_transform
from pixtreme.transform.affine import get_inverse_matrix
from pixtreme.utils.dlpack import to_cupy
from pixtreme.utils.dlpack import to_numpy
from pixtreme.utils.dtypes import to_float32
import typing
__all__ = ['GaussianBlur', 'PasteBack', 'affine_transform', 'cp', 'get_inverse_matrix', 'np', 'paste_back', 'to_cupy', 'to_float32', 'to_numpy']
class PasteBack:
    def __init__(self):
        ...
    def create_mask(self, size: tuple):
        ...
    def get(self, target_image: np.ndarray | cp.ndarray, paste_image: np.ndarray | cp.ndarray, M) -> np.ndarray | cp.ndarray:
        ...
def paste_back(target_image: cp.ndarray, paste_image: cp.ndarray, M: cp.ndarray, mask: cp.ndarray = None) -> cp.ndarray:
    ...
__test__: dict = {}

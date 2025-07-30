from __future__ import annotations
import builtins as __builtins__
import cupy as cp
import numpy as np
import onnxruntime as onnxruntime
from pixtreme.color.bgr import bgr_to_rgb
from pixtreme.color.bgr import rgb_to_bgr
from pixtreme.face.schema import Face
from pixtreme.transform.affine import crop_from_kps
from pixtreme.transform.resize import resize
from pixtreme.utils.blob import to_blob
from pixtreme.utils.dlpack import to_cupy
from pixtreme.utils.dlpack import to_numpy
from pixtreme.utils.dtypes import to_float32
import typing
__all__ = ['Face', 'FaceDetection', 'INTER_AUTO', 'bgr_to_rgb', 'cp', 'crop_from_kps', 'np', 'onnxruntime', 'resize', 'rgb_to_bgr', 'to_blob', 'to_cupy', 'to_float32', 'to_numpy']
class FaceDetection:
    def __init__(self, model_path: str | None = None, model_bytes: bytes | None = None, device_id: int = 0, device: str = 'cuda') -> None:
        ...
    def _init_vars(self):
        ...
    def crop(self, image: cp.ndarray, kps: cp.ndarray, size: int = 512) -> tuple:
        ...
    def distance2bbox(self, points: cp.ndarray, distance: cp.ndarray, max_shape = None) -> cp.ndarray:
        ...
    def distance2kps(self, points: cp.ndarray, distance: cp.ndarray, max_shape = None) -> cp.ndarray:
        ...
    def forward(self, image, threshold):
        ...
    def get(self, image, crop_size = 512, max_num = 0, metric = 'default'):
        ...
    def nms(self, dets):
        ...
INTER_AUTO: int = -1
__test__: dict = {}

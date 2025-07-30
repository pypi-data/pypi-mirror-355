from __future__ import annotations
import builtins as __builtins__
import numpy as np
import onnxruntime as onnxruntime
from pixtreme.color.bgr import bgr_to_rgb
from pixtreme.color.bgr import rgb_to_bgr
from pixtreme.face.emap import load_emap
from pixtreme.face.schema import Face
from pixtreme.transform.resize import resize
from pixtreme.utils.blob import to_blob
from pixtreme.utils.dlpack import to_cupy
from pixtreme.utils.dlpack import to_numpy
import typing
__all__ = ['Face', 'FaceSwap', 'INTER_AUTO', 'bgr_to_rgb', 'load_emap', 'np', 'onnxruntime', 'resize', 'rgb_to_bgr', 'to_blob', 'to_cupy', 'to_numpy']
class FaceSwap:
    def __init__(self, model_path: str | None = None, model_bytes: bytes | None = None, device_id: int = 0, device: str = 'cuda'):
        ...
    def forward(self, img, latent) -> np.ndarray:
        ...
    def get(self, target_face: Face, source_face: Face) -> np.ndarray:
        ...
INTER_AUTO: int = -1
__test__: dict = {}

from __future__ import annotations
import builtins as __builtins__
import os as os
from spandrel.__helpers.loader import ModelLoader
import spandrel_extra_arches as ex_arch
import sys as sys
import tensorrt as trt
import torch as torch
import typing
__all__ = ['ModelLoader', 'ex_arch', 'onnx_to_trt', 'os', 'sys', 'torch', 'torch_to_onnx', 'trt']
def onnx_to_trt(onnx_path: str, engine_path: str, precision: str = 'fp16', workspace: int = 1073741824) -> None:
    ...
def torch_to_onnx(model_path: str, onnx_path: str, input_shape: tuple = (1, 3, 1080, 1920), opset_version: int = 20, precision: str = 'fp32', dynamic_axes: dict | None = None, device: str = 'cuda') -> None:
    ...
__test__: dict = {}

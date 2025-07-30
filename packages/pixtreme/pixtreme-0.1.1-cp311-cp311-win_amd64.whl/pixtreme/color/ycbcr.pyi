from __future__ import annotations
import builtins as __builtins__
import cupy as cp
import cupy._core.raw
from pixtreme.color.bgr import bgr_to_rgb
from pixtreme.color.bgr import rgb_to_bgr
__all__ = ['bgr_to_rgb', 'bgr_to_ycbcr', 'cp', 'rgb_to_bgr', 'rgb_to_ycbcr', 'rgb_to_ycbcr_kernel', 'rgb_to_ycbcr_kernel_code', 'ycbcr_to_bgr', 'ycbcr_to_grayscale', 'ycbcr_to_rgb', 'ycbcr_to_rgb_kernel', 'ycbcr_to_rgb_kernel_code']
def bgr_to_ycbcr(image: cp.ndarray) -> cp.ndarray:
    ...
def rgb_to_ycbcr(image: cp.ndarray) -> cp.ndarray:
    """
    
        Convert RGB to YCbCr
    
        Parameters
        ----------
        image : cp.ndarray
            Input frame. Shape 3D array (height, width, 3) in RGB format.
    
        Returns
        -------
        image_ycbcr : cp.ndarray
            Output frame. Shape 3D array (height, width, 3) in YCbCr format.
        
    """
def ycbcr_to_bgr(image: cp.ndarray) -> cp.ndarray:
    ...
def ycbcr_to_grayscale(image: cp.ndarray) -> cp.ndarray:
    """
    
        YCbCr to Grayscale conversion
    
        Parameters
        ----------
        image : cp.ndarray
            Input frame. Shape 3D array (height, width, 3) in YCbCr 4:4:4 format.
    
        Returns
        -------
        image_gray : cp.ndarray
            Grayscale frame. Shape 3D array (height, width, 3) in RGB 4:4:4 format.
        
    """
def ycbcr_to_rgb(image: cp.ndarray) -> cp.ndarray:
    """
    
        Convert YCbCr to RGB
    
        Parameters
        ----------
        image : cp.ndarray
            Input frame. Shape 3D array (height, width, 3) in YCbCr format.
    
        Returns
        -------
        frame_rgb : cp.ndarray
            Output frame. Shape 3D array (height, width, 3) in RGB format.
        
    """
__test__: dict = {}
rgb_to_ycbcr_kernel: cupy._core.raw.RawKernel  # value = <cupy._core.raw.RawKernel object>
rgb_to_ycbcr_kernel_code: str = '\nextern "C" __global__\nvoid rgb_to_ycbcr_kernel(const float* rgb, float* ycbcr, int width, int height) {\n    int x = blockIdx.x * blockDim.x + threadIdx.x;\n    int y = blockIdx.y * blockDim.y + threadIdx.y;\n    if (x >= width || y >= height) return;\n\n    int idx = (y * width + x) * 3;\n    float r = rgb[idx];\n    float g = rgb[idx + 1];\n    float b = rgb[idx + 2];\n\n    float y_component = 0.2126f * r + 0.7152f * g + 0.0722f * b;\n    float cb_component = -0.114572f * r - 0.385428f * g + 0.5f * b + 0.5f;\n    float cr_component = 0.5f * r - 0.454153f * g - 0.045847f * b + 0.5f;\n\n    // to legal range\n    y_component = (y_component * 219.0f + 16.0f) / 255.0f;\n    cb_component = (cb_component * 224.0f + 16.0f) / 255.0f;\n    cr_component = (cr_component * 224.0f + 16.0f) / 255.0f;\n\n    ycbcr[idx] = y_component;\n    ycbcr[idx + 1] = cb_component;\n    ycbcr[idx + 2] = cr_component;\n}\n'
ycbcr_to_rgb_kernel: cupy._core.raw.RawKernel  # value = <cupy._core.raw.RawKernel object>
ycbcr_to_rgb_kernel_code: str = '\nextern "C" __global__\nvoid ycbcr_to_rgb_kernel(const float* ycbcr, float* rgb, int width, int height) {\n    int x = blockIdx.x * blockDim.x + threadIdx.x;\n    int y = blockIdx.y * blockDim.y + threadIdx.y;\n    if (x >= width || y >= height) return;\n\n    int idx = (y * width + x) * 3;\n    float y_component = ycbcr[idx];\n\n    // 10bit precision\n    float cb_component = ycbcr[idx + 1] - 0.5004887f;\n    float cr_component = ycbcr[idx + 2] - 0.5004887f;\n    const float under_offset_16 = 0.0625610f;\n\n    // 8bit precision\n    //float cb_component = ycbcr[idx + 1] - 0.5019607f;\n    //float cr_component = ycbcr[idx + 2] - 0.5019607f;\n    //const float under_offset_16 = 0.0627450f;\n\n    // 709\n    //float r = y_component + 1.5748037f * cr_component;\n    //float g = y_component - 0.1873261f * cb_component - 0.4681249f * cr_component;\n    //float b = y_component + 1.8555993f * cb_component;\n\n    // 709 legal\n    float r = 1.1643835 * (y_component - under_offset_16) + 1.5960267f * cr_component;\n    float g = 1.1643835 * (y_component - under_offset_16) - 0.3917622f * cb_component - 0.8129676 * cr_component;\n    float b = 1.1643835 * (y_component - under_offset_16) + 2.0172321f * cb_component;\n\n    // 601\n    //float r = y_component + 1.402f * cr_component;\n    //float g = y_component - 0.344136f * cb_component - 0.714136 * cr_component;\n    //float b = y_component + 1.772f * cb_component;\n\n\n    rgb[idx] = r;\n    rgb[idx + 1] = g;\n    rgb[idx + 2] = b;\n}\n'

"""
This module provides various activation functions for tensors.
"""

from __future__ import annotations
import numpy as np

from .tensor import Tensor
from .grad import (
    tanh_backward,
    relu_backward,
    sigmoid_backward,
    softmax_backward
)

def tanh(tensor: Tensor) -> Tensor:
    """
    Element-wise hyperbolic tangent activation function.
    
    Args:
        tensor (Tensor): Input tensor.
        
    Returns:
        Tensor: A new tensor containing the hyperbolic tangent of the input tensor.
    """
    
    new_tensor = Tensor._create_node(
        data=np.tanh(tensor._data),
        grad_fn=tanh_backward,
        parents=(tensor,)
    )
    return new_tensor

def relu(tensor: Tensor) -> Tensor:
    """
    Element-wise Rectified Linear Unit (ReLU) activation function.
    
    Args:
        tensor (Tensor): Input tensor.
        
    Returns:
        Tensor: A new tensor containing the ReLU activation of the input tensor.
    """

    new_tensor = Tensor._create_node(
        data=np.maximum(0, tensor._data),
        grad_fn=relu_backward,
        parents=(tensor,)
    )
    return new_tensor

def sigmoid(tensor: Tensor) -> Tensor:
    """
    Element-wise sigmoid activation function.
    
    Args:
        tensor (Tensor): Input tensor.
        
    Returns:
        Tensor: A new tensor containing the sigmoid activation of the input tensor. 
    """
    
    new_tensor = Tensor._create_node(
        data=1 / (1 + np.exp(-tensor._data)),
        grad_fn=sigmoid_backward,
        parents=(tensor,)
    )
    return new_tensor

def softmax(tensor: Tensor, axis=-1) -> Tensor:
    """
    Element-wise softmax activation function.
    
    Args:
        tensor (Tensor): Input tensor.
        axis (int): Axis along which to compute the softmax. Default is -1 (last axis).
        
    Returns:
        Tensor: A new tensor containing the softmax activation of the input tensor.
    """
    
    x_shifted = tensor._data - np.max(tensor._data, axis=axis, keepdims=True)
    exp_x = np.exp(x_shifted)
    softmax_output = exp_x / np.sum(exp_x, axis=axis, keepdims=True)
    
    new_tensor = Tensor._create_node(
        data=softmax_output,
        grad_fn=softmax_backward,
        parents=(tensor,),
        extra={'axis': axis}
    )
    return new_tensor
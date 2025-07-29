"""
This module provides functions to compute various loss functions.
"""

from __future__ import annotations

from .tensor import Tensor
from .grad import mse_backward, mae_backward
from .math import mean, abs

def mse_loss(pred: Tensor, target: Tensor) -> Tensor:
    """
    Computes the Mean Squared Error (MSE) loss between the predicted and target tensors.
    
    Args:
        pred (Tensor): The predicted tensor.
        target (Tensor): The target tensor.
        
    Returns:
        Tensor: The MSE loss tensor.
    """
    
    if pred._shape != target._shape:
        raise ValueError("Predicted and target tensors must have the same shape for MSE loss.")
    
    diff = pred - target
    mse = mean(diff * diff)
    
    return mse
    
def mae_loss(pred: Tensor, target: Tensor) -> Tensor:
    """
    Computes the Mean Absolute Error (MAE) loss between the predicted and target tensors.
    
    Args:
        pred (Tensor): The predicted tensor.
        target (Tensor): The target tensor.
        
    Returns:
        Tensor: The MAE loss tensor.
    """
    
    if pred._shape != target._shape:
        raise ValueError("Predicted and target tensors must have the same shape for MAE loss.")
    
    diff = pred - target
    mae = mean(abs(diff))
    
    return mae
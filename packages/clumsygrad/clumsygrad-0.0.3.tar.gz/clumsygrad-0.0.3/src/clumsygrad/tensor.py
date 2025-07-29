"""
This module contains the Tensor class implementation for automatic differentiation.
It supports basic tensor operations, tracks gradients, and can be used to build computational graphs for backpropagation.
It also contains some utility functions for managing tensors and their gradients.
"""

from __future__ import annotations
import numpy as np
from typing import Dict, Set, Union, List, Tuple, Optional, Callable
import weakref

from .grad import *
from .types import TensorType

class Tensor:
    """
    A tensor class for automatic differentiation.
    This class supports basic tensor operations and tracks gradients.
    It is used to build computational graphs for backpropagation.
    """
    
    _global_tensor_registry = weakref.WeakValueDictionary()
    _id_counter = 0
    
    __slots__ = ('_data', '_shape', '_id', '_grad_fn',
                 '_grad', '_children', '_parents', '_stale',
                 '_extra', '_version', '_tensor_type', '_requires_grad', '__weakref__')
    
    @staticmethod
    def _create_node(data: np.ndarray, 
                     grad_fn: Optional[Callable], 
                     parents: Tuple[Tensor, ...],
                     extra: Optional[dict] = None) -> Tensor:
        
        """
        Creates a new tensor node in the computational graph.
        
        Args:
            data: The data for the new tensor.
            grad_fn: The gradient function to use for backpropagation.
            parents: The parent tensors that this tensor depends on.
            extra: Additional metadata for the tensor (optional).
            
        Returns:
            A new Tensor instance representing the node in the computational graph. 
        """
        
        node = Tensor(data=data, tensor_type=TensorType.INTERMEDIATE)
        node._grad_fn = grad_fn
        node._parents = parents
        node._requires_grad = any(parent._requires_grad for parent in parents)
        
        if extra: node._extra.update(extra)
        for parent in parents: parent._children.append(node)
        
        return node
    
    @staticmethod
    def clear_stale_tensors():
        """
        Remove all tensors that are marked as stale from memory.
        This is required to prevent unnecessary tensor objects from accumulating in memory.
        """
        
        for tensor in list(Tensor._global_tensor_registry.values()):
            if tensor._stale:
                for parent in tensor._parents:
                    parent._children.remove(tensor)
                for child in tensor._children:
                    child._parents = tuple(p for p in child._parents if p._id != tensor._id)
                del Tensor._global_tensor_registry[tensor._id]
    
    def __init__(self, 
                 data,
                 tensor_type: TensorType = TensorType.INPUT,
                ):
        """
        Initialize a new tensor.
        
        Args:
            data: The initial data for the tensor.
            tensor_type: The type of the tensor, as TensorType.INPUT/PARAMETER/INTERMEDIATE.
            
        Note: 
            The tensor will not track/propagate gradients if it is of type INPUT.
            If it is of type PARAMETER, it will be treated as a trainable parameter.
            Using INTERMEDIATE tensor type is nuanced and not recommended 
            unless you are explicitly creating a node in the graph.
        """
        
        self._data = np.array(data, dtype=np.float32)
        self._shape = self._data.shape
        self._grad_fn = None
        self._grad = None
        self._tensor_type = tensor_type
        
        if self._tensor_type == TensorType.PARAMETER:
            self._requires_grad = True
        else:
            self._requires_grad = False
        
        self._stale = False
        self._parents: Tuple[Tensor, ...] = ()
        self._children: List[Tensor] = []
        
        self._id = Tensor._id_counter
        Tensor._id_counter += 1
        self._version = 0
        
        self._extra = {}
        Tensor._global_tensor_registry[self._id] = self
    
    def __repr__(self):
        grad_fn_name = self._grad_fn.__name__ if self._grad_fn else None
        return (f"Tensor(id={self._id}, shape={self._shape}, "
                f"tensor_type={self._tensor_type.name}, "
                f"grad_fn={grad_fn_name}, "
                f"requires_grad={self._requires_grad})")
    
    @property
    def data(self) -> np.ndarray:
        """Return the data of the tensor."""
        return self._data
    
    @property
    def shape(self) -> tuple:
        """Return the shape of the tensor."""
        return self._shape
    
    @property
    def grad(self) -> Optional[np.ndarray]:
        """Return the gradient of the tensor."""
        return self._grad
    
    @grad.setter
    def grad(self, value: np.ndarray):
        """Set the gradient of the tensor."""
        self._grad = value
    
    @property
    def requires_grad(self) -> bool:
        """Return whether this tensor requires gradients."""
        return self._requires_grad
    
    def T(self) -> Tensor:
        """Returns a transpose of the tensor."""
        new_tensor = None
        
        if (self._grad_fn == transpose_backward and len(self._parents) == 1):
            self._stale = True
            new_tensor = self._parents[0]
        else:
            new_tensor = Tensor._create_node(
                data=self._data.T,
                grad_fn=transpose_backward,
                parents=(self,),
            )
        
        return new_tensor
    
    def __add__(self, other: Union[Tensor, float]) -> Tensor:
        if isinstance(other, Tensor):
            if self._shape != other._shape:
                raise ValueError(f"Shape mismatch for addition: {self._shape} vs {other._shape}")
            
            new_tensor = Tensor._create_node(
                data=self._data + other._data,
                grad_fn=add_backward,
                parents=(self, other),
            )
        else:
            new_tensor = Tensor._create_node(
                data=self._data + other,
                grad_fn=add_scalar_backward,
                parents=(self,),
                extra={'scalar_value': float(other)}
            )
        
        return new_tensor
    
    def __sub__(self, other: Union[Tensor, float]) -> Tensor:
        if isinstance(other, Tensor):
            if self._shape != other._shape:
                raise ValueError(f"Shape mismatch for subtraction: {self._shape} vs {other._shape}")
            
            new_tensor = Tensor._create_node(
                data=self._data - other._data,
                grad_fn=sub_backward,
                parents=(self, other),
            )
        else:
            new_tensor = Tensor._create_node(
                data=self._data - other,
                grad_fn=sub_scalar_backward,
                parents=(self,),
                extra={'scalar_value': float(other)}
            )
        
        return new_tensor
    
    def __mul__(self, other: Union[Tensor, float]) -> Tensor:
        if isinstance(other, Tensor):
            if self._shape != other._shape:
                raise ValueError(f"Shape mismatch for multiplication: {self._shape} vs {other._shape}")
            
            new_tensor = Tensor._create_node(
                data=self._data * other._data,
                grad_fn=mul_backward,
                parents=(self, other),
            )
        else:
            new_tensor = Tensor._create_node(
                data=self._data * other,
                grad_fn=mul_scalar_backward,
                parents=(self,),
                extra={'scalar_value': float(other)}
            )
        
        return new_tensor
    
    def __matmul__(self, other: Tensor) -> Tensor:
        if not isinstance(other, Tensor):
            raise TypeError("Right operand must be a Tensor for matrix multiplication.")
        
        if len(self._shape) < 2 or len(other._shape) < 2:
            raise ValueError("Matrix multiplication requires at least 2D tensors.")
        
        if self._shape[-1] != other._shape[-2]:
            raise ValueError(f"Matrix shapes not aligned: {self._shape} @ {other._shape}")
        
        new_tensor = Tensor._create_node(
            data=self._data @ other._data,
            grad_fn=matmul_backward,
            parents=(self, other),
        )
        return new_tensor
    
    def __pow__(self, power: float) -> Tensor:
        new_tensor = Tensor._create_node(
            data=self._data ** power,
            grad_fn=power_backward,
            parents=(self,),
            extra={'power': float(power)}
        )
        return new_tensor
    
    def __neg__(self) -> Tensor:
        new_tensor = Tensor._create_node(
            data=-self._data,
            grad_fn=negate_backward,
            parents=(self,),
        )
        return new_tensor
    
    def reshape(self, new_shape: Tuple[int, ...]) -> Tensor:
        """
        Reshape the tensor to a new shape.
        
        Args:
            new_shape: The desired shape for the tensor.
            
        Returns:
            A new Tensor with the reshaped data.
            
        Raises:
            ValueError: If the new shape does not have the same number of elements as the original shape.
        """
    
        if np.prod(new_shape) != np.prod(self._shape):
            raise ValueError("New shape must have the same number of elements as the original shape.")
        
        new_tensor = Tensor._create_node(
            data=self._data.reshape(new_shape),
            grad_fn=reshape_backward,
            parents=(self,),
            extra={'original_shape': self._shape}
        )
        return new_tensor
    
    def backward(self, gradient: Optional[np.ndarray] = None, keep_grads: bool = False):
        """
        backward pass to compute gradients.
        
        Args:
            gradient: Optional gradient to start the backward pass. If None, it assumes a scalar output and uses ones.
            keep_grads: If True, keeps gradients for all nodes in the graph. If False, clears gradients for intermediate nodes.
            
        Raises:
            RuntimeError: If the tensor does not require gradients or if the gradient is not compatible.
        """
        
        Tensor.clear_stale_tensors()
        
        if not self._requires_grad:
            raise RuntimeError("Tensor does not require gradients")
        
        if gradient is None:
            if self._data.size != 1:
                raise RuntimeError("Gradient can only be implicitly created for scalar outputs")
            gradient = np.ones_like(self._data)
        
        topo_order: List[Tensor] = []
        visited: Set[Tensor] = set()
        
        def build_topo(node: Tensor):
            if node._id in visited or not node._requires_grad:
                return
            visited.add(node._id)
            
            for parent in node._parents:
                build_topo(parent)
            topo_order.append(node)
        
        build_topo(self)
        
        self._grad = gradient
        
        for node in reversed(topo_order):
            if node._grad_fn and node._grad is not None:
                gradients = node._grad_fn(node, node._grad)
                
                for parent, grad in zip(node._parents, gradients):
                    if parent._requires_grad:
                        if parent._grad is None:
                            parent._grad = grad
                        else:
                            parent._grad = parent._grad + grad
            
                # If the node is an intermediate node and we are not keeping gradients,
                # we clear its gradient to save memory.
                if not keep_grads and node._tensor_type == TensorType.INTERMEDIATE and node != self:      
                    node._grad = None
            
class TensorUtils:
    @staticmethod
    def get_parameters(tensor: Tensor) -> List[Tensor]:
        """
        Collect all parameters in the computational graph starting from the given tensor.
        
        Args:
            tensor: The starting tensor from which to collect parameters.
            
        Returns:
            A list of Tensor objects that are parameters in the graph.
        """
        
        parameters = []
        visited = set()
        
        def collect_params(node):
            if node._id in visited:
                return
            visited.add(node._id)
            
            if node._tensor_type == TensorType.PARAMETER:
                parameters.append(node)
            
            for child in (node._parents or []):
                collect_params(child)
        
        collect_params(tensor)
        return parameters
    
    @staticmethod
    def count_by_type(tensor: Tensor) -> Dict[TensorType, int]:
        """
        Counts the number of tensors of each type in the computational graph starting from the given tensor.
        
        Args:
            tensor: The starting tensor from which to count tensor types.
            
        Returns:
            A dictionary with counts of each tensor type (INPUT, PARAMETER, INTERMEDIATE).
        """
        
        counts = {TensorType.INPUT: 0, TensorType.PARAMETER: 0, TensorType.INTERMEDIATE: 0}
        visited = set()
        
        def count_nodes(node):
            if node._id in visited:
                return
            visited.add(node._id)
            counts[node._tensor_type] += 1
            
            for child in (node._parents or []):
                count_nodes(child)
        
        count_nodes(tensor)
        return counts
"""
This module defines the TensorType enumeration, which categorizes tensors in a computation graph.
"""

from enum import IntEnum
    
class TensorType(IntEnum):
    """
    The type of a tensor in the computation graph, which can be one of the following:
    
    Types:
        INPUT: A tensor that is an input to the computation graph,
        PARAMETER: A tensor that is a parameter of the model, a trainable block,
        INTERMEDIATE: A tensor that is an intermediate result in the computation graph.
        
    """
    
    INPUT = 0
    PARAMETER = 1
    INTERMEDIATE = 2 
# ClumsyGrad

[![PyPI version](https://badge.fury.io/py/clumsygrad.svg)](https://badge.fury.io/py/clumsygrad)
[![Docs](https://readthedocs.org/projects/clumsygrad/badge/?version=latest)](https://clumsygrad.readthedocs.io/en/latest/)

**ClumsyGrad** is a minimal Python library for automatic differentiation, built on top of NumPy. It provides a `Tensor` class that supports various mathematical operations and automatically computes gradients via backpropagation, making it a great tool for learning the fundamentals of deep learning frameworks.

## Features

- **Dynamic Computational Graphs**: Define and run computations on the fly.
- **Automatic Differentiation**: Compute gradients automatically using the chain rule.
- **NumPy Backend**: Leverages NumPy for efficient numerical operations.
- **Basic Tensor Operations**: Supports addition, subtraction, multiplication, matrix multiplication, power, transpose, sum, mean, exp, log, abs, and reshape.
- **Easy to Understand**: Designed with simplicity in mind, ideal for educational purposes.

## Installation

You can install ClumsyGrad using pip:

```shell
pip install clumsygrad
```

## Quick Start

Here's a brief overview of how to use ClumsyGrad:

### Creating Tensors

```python
from clumsygrad.tensor import Tensor
from clumsygrad.types import TensorType
import numpy as np

# Create a tensor from a list (defaults to TensorType.INPUT)
a = Tensor([1.0, 2.0, 3.0])
print(a)
# Output: Tensor(id=0, shape=(3,), tensor_type=INPUT, grad_fn=None, requires_grad=False)

# Create a tensor that requires gradients (e.g., a parameter)
b = Tensor([[4.0], [5.0], [6.0]], tensor_type=TensorType.PARAMETER)
print(b)
# Output: Tensor(id=1, shape=(3, 1), tensor_type=PARAMETER, grad_fn=None, requires_grad=True)

# Create a tensor from a NumPy array
c_data = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)
c = Tensor(c_data, tensor_type=TensorType.PARAMETER)
print(c)
# Output: Tensor(id=2, shape=(2, 2), tensor_type=PARAMETER, grad_fn=None, requires_grad=True)
```

### Performing Operations

ClumsyGrad tensors support various operations:

```python
from clumsygrad.tensor import Tensor
from clumsygrad.types import TensorType

# Define some tensors
x = Tensor([2.0, 3.0], tensor_type=TensorType.PARAMETER)
y = Tensor([4.0, 5.0], tensor_type=TensorType.PARAMETER)
s = Tensor(10.0, tensor_type=TensorType.PARAMETER) # A scalar tensor

# Addition
z_add = x + y
print(f"x + y = {z_add.data}")
# Output: x + y = [6. 7.]

# Element-wise multiplication
z_mul = x * y
print(f"x * y = {z_mul.data}")
# Output: x * y = [ 8. 15.]

# Scalar multiplication
z_scalar_mul = x * s # or x * 10.0
print(f"x * s = {z_scalar_mul.data}")
# Output: x * s = [20. 30.]

# Power
z_pow = x ** 2
print(f"x ** 2 = {z_pow.data}")
# Output: x ** 2 = [4. 9.]

# Matrix multiplication
mat_a = Tensor([[1, 2], [3, 4]], tensor_type=TensorType.PARAMETER)
mat_b = Tensor([[5, 6], [7, 8]], tensor_type=TensorType.PARAMETER)
mat_c = mat_a @ mat_b
print(f"mat_a @ mat_b = \n{mat_c.data}")
# Output: mat_a @ mat_b =
# [[19. 22.]
#  [43. 50.]]
```

### Automatic Differentiation (Backpropagation)

Let's compute gradients for a simple function `L = (a * b + c).sum()`:

```python
from clumsygrad.tensor import Tensor
from clumsygrad.types import TensorType
import numpy as np

# Define input tensors that require gradients
a = Tensor([2.0, 3.0], tensor_type=TensorType.PARAMETER)
b = Tensor([4.0, 1.0], tensor_type=TensorType.PARAMETER)
c = Tensor([-1.0, 2.0], tensor_type=TensorType.PARAMETER)

# Define the computation
# x = a * b  => x = [8.0, 3.0]
# y = x + c  => y = [7.0, 5.0]
# L = y.sum() => L = 12.0
x = a * b
y = x + c
L = y.sum()

print(f"L = {L.data}")
# Output: L = 12.0

# Perform backpropagation
L.backward()

# Access the gradients
print(f"Gradient of L with respect to a (dL/da): {a.grad}")
# Output: Gradient of L with respect to a (dL/da): [4. 1.]
# (dL/da_i = b_i)

print(f"Gradient of L with respect to b (dL/db): {b.grad}")
# Output: Gradient of L with respect to b (dL/db): [2. 3.]
# (dL/db_i = a_i)

print(f"Gradient of L with respect to c (dL/dc): {c.grad}")
# Output: Gradient of L with respect to c (dL/dc): [1. 1.]
# (dL/dc_i = 1)
```

## Contributing

Contributions are welcome! If you'd like to contribute, please feel free to fork the repository, make your changes, and submit a pull request. You can also open an issue if you find a bug or have a feature request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

For more detailed information, tutorials, and API reference, please check out the official documentation:

[https://clumsygrad.readthedocs.io/en/latest/](https://clumsygrad.readthedocs.io/en/latest/)

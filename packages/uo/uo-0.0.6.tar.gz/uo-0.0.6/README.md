# uo
pipeline computing

To install:	```pip install uo```

## Overview
The `uo` package provides a framework for creating and managing computation pipelines. This functionality is particularly useful for scenarios where a sequence of data transformations and computations need to be applied in a specific order. The core of the package is the `ComputationPipeline` class which allows users to compose a pipeline of callable objects (functions, methods, etc.) that are executed sequentially.

## Features
- **Composable Pipelines**: Easily compose multiple callable objects into a single callable pipeline.
- **Flexible Step Definition**: Each step in the pipeline can be defined with a callable and its associated method to call, allowing for great flexibility in how operations are performed.
- **Partial Argument Binding**: Steps can include partial argument binding using the `partial` function from Python's `functools`, providing more control over how functions are called within the pipeline.

## ComputationPipeline Class
The `ComputationPipeline` class is designed to chain a sequence of operations together. Each step in the pipeline is defined by a tuple that specifies the name of the step, the object (function or class instance), and optionally, the method name to call on the object (default is `__call__`). The pipeline can be executed by calling the instance with the appropriate arguments.

### Constructor
```python
def __init__(self, steps):
    """
    Initializes a new instance of the ComputationPipeline.

    :param steps: A list of tuples. Each tuple should contain:
        - func_name: A string representing the name of the function or method.
        - obj: The function or object that will be called.
        - call_method (optional): The method name to call on the object. If not provided, '__call__' is assumed.
    """
```

### Usage Example
```python
# Define a simple pipeline with two steps
f = ComputationPipeline(steps=[
    ('increment', lambda x: x + 2),
    ('multiply', lambda x: x * 10)
])

# Execute the pipeline
result = f(1)  # (1 + 2) * 10 = 30
print(result)  # Output: 30
```

## Advanced Usage
You can also specify methods of objects or use partial functions to pre-specify some arguments:

```python
from functools import partial

# Assuming an object with methods that take additional parameters
class MathOperations:
    def multiply(self, x, factor):
        return x * factor

    def add(self, x, increment):
        return x + increment

math_ops = MathOperations()

# Create a pipeline using methods from the MathOperations class
g = ComputationPipeline(steps=[
    ('add', math_ops, 'add'),
    ('multiply', partial(math_ops.multiply, factor=5))
])

# Execute the pipeline
result = g(3)  # (3 + 0) * 5 = 15
print(result)  # Output: 15
```

This package is ideal for scenarios where data needs to be processed in distinct, sequential steps, such as data preprocessing, feature engineering, or even in a machine learning inference pipeline.
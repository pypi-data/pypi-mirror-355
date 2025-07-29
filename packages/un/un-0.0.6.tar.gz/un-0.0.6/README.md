# un
Analyzing classes

To install:	```pip install un```

The `un` package provides a suite of tools for analyzing Python classes, particularly focusing on method resolution order (MRO), method overrides, and interactions with superclass methods. It allows users to inspect how methods are resolved across class hierarchies, identify which classes implement specific methods, and trace method calls to `super`. This can be particularly useful for debugging complex inheritance structures and ensuring that method overrides behave as expected.

## Main Features

- **Method Resolution Analysis**: Trace the resolution path of any method through the MRO of a class.
- **Super Method Calls**: Identify calls to `super()` within methods, helping to understand how subclasses interact with superclass methods.
- **Class and Method Identifiers**: Customize how classes and methods are identified in outputs, with options for full module paths, class names, or direct class objects.
- **DataFrame Outputs**: Generate Pandas DataFrame objects that neatly represent method resolutions and class methods for easier analysis.
- **MRO Visualization**: Print or visualize the method resolution order with options to include indents for better readability.

## Usage Examples

### Analyzing Method Resolutions

You can analyze how methods are resolved within a class hierarchy using the `method_resolutions` function. This function returns a dictionary where keys are method names and values are lists of classes that resolve these methods, in order.

```python
from un import method_resolutions

class A:
    def foo(self):
        return 42

class B(A):
    def foo(self):
        super().foo()

resolutions = method_resolutions(B, ['foo'], cls_identifier='name')
print(resolutions)
```

### DataFrame of Method Resolutions

For a more visual representation, you can convert the method resolutions into a Pandas DataFrame:

```python
from un import df_of_method_resolutions

df = df_of_method_resolutions(B, ['foo'], cls_identifier='name')
print(df)
```

### Printing the MRO with Indents

To visualize the MRO of a class with indents highlighting the inheritance structure:

```python
from un import print_mro

print_mro(B)
```

### Finding Methods Calling Super

To find out if a method in a class calls a super method of the same name:

```python
from un import method_calls_super_method_of_same_name

print(method_calls_super_method_of_same_name(B.foo))
```

## Documentation

Below is a brief documentation of some key functions and classes:

- `method_resolutions(cls, methods=None, cls_identifier='name', method_not_found_error=True, include_overridden_methods=False)`: Analyze method resolutions for a given class.
- `df_of_method_resolutions(cls, methods=None, cls_identifier='name', method_not_found_error=True, include_overridden_methods=False)`: Returns a DataFrame representing the method resolutions of a class.
- `print_mro(cls, indent=4)`: Print the MRO of a class, visually indented to show the hierarchy.
- `MethodNotFoundInMro`: Exception raised when a method is not found in the MRO of a class during analysis.

These tools are designed to help developers understand and debug class hierarchies in Python, making it easier to work with complex object-oriented code.
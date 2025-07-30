# uf
Utils to work with python objects

To install:	```pip install uf```

## Description
The `uf` package provides a collection of utilities designed to facilitate operations on Python objects. These utilities include functions for copying attributes between objects, checking and modifying method types, serializing objects with compression, and dynamically managing object attributes. The package is structured to aid in reflection, introspection, and dynamic modification of objects, which can be particularly useful in advanced Python programming scenarios such as metaprogramming or dynamic attribute manipulation.

## Main Functionalities
- **Attribute Copying**: Copy specified attributes from one object to another, optionally raising an error if the source object does not have one of the requested attributes.
- **Class and Instance Utilities**: Determine if a method is a class method, list properties and methods of classes and objects, and inject methods into objects at runtime.
- **Serialization**: Compress and decompress serialized Python objects using `pickle` and `zlib` for efficient storage or transmission.
- **Attribute Management**: Set attributes on objects dynamically from a dictionary, check for attributes, and differentiate between callable and non-callable attributes.

## Usage Examples

### Copying Attributes
Copy attributes from one object to another with control over error handling when attributes are missing:
```python
class Source:
    x = 10
    y = 20

class Target:
    x = 5

# Copy 'x' and 'y' from Source to Target
copy_attrs(Target, Source, ['x', 'y'])
print(Target.x)  # Output: 10
print(Target.y)  # Output: 20
```

### Checking and Injecting Methods
Check if a method is a class method and inject a new method into an instance:
```python
class MyClass:
    @classmethod
    def cls_method(cls):
        print("This is a class method.")

# Check if 'cls_method' is a class method
print(is_classmethod(MyClass, 'cls_method'))  # Output: True

# Inject a new method into an instance
instance = MyClass()
def new_method(self):
    print("This is a new method.")
inject_method(instance, new_method)
instance.new_method()  # Output: "This is a new method."
```

### Serialization and Compression
Serialize and compress an object, then decompress and deserialize:
```python
my_data = {'key': 'value'}
compressed = zpickle_dumps(my_data)
original = zpickle_loads(compressed)
print(original)  # Output: {'key': 'value'}
```

### Dynamic Attribute Management
Set attributes on an object dynamically and check for their existence:
```python
class MyObject:
    pass

obj = MyObject()
set_attributes(obj, {'new_attr': 123, 'another_attr': 'hello'})
print(obj.new_attr)  # Output: 123
print(has_attributes(obj, ['new_attr', 'another_attr']))  # Output: True
```

## Function and Class Documentation
Each function in the `uf` package is documented with docstrings, providing a detailed explanation of its behavior, parameters, and usage examples. These docstrings can be viewed directly in the source code or through Python's built-in help system using `help(function_name)`.

For further details and advanced usage, users are encouraged to refer to the source code which is well-commented and structured to be self-explanatory.
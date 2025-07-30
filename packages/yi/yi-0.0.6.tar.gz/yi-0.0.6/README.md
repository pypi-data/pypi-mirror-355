# yi
Convert dictionaries to other objects

To install:	```pip install yi```

## Overview
The `yi` package provides a collection of utilities for transforming, analyzing, and handling dictionaries in Python. It offers functions to convert dictionaries into different formats, manipulate dictionary keys and values, and create structured objects from dictionaries. This package is useful for data manipulation, especially when dealing with configurations, data records, or any structured data represented as dictionaries.

## Features
- **Tuple Conversion**: Convert dictionaries into a list of tuples, making it easy to reconstruct the original dictionary or manipulate dictionary items.
- **Table String Representation**: Generate a formatted string representing the dictionary as a table, which is useful for logging or displaying dictionary contents in a readable format.
- **Namedtuple Creation**: Create namedtuples from dictionaries, allowing for the use of dot notation to access dictionary values.
- **Hashable Dictionary**: Provides a hashable dictionary class that can be used as keys in other dictionaries or stored in sets.
- **Struct Class**: A flexible class that converts nested dictionaries into objects that can be accessed using attribute notation.
- **Dictionary Inversion**: Functions to invert dictionaries, supporting one-to-one, one-to-many, and many-to-one mappings.
- **Word Replacement in Strings**: Replace words in text based on a dictionary mapping, with support for regular expressions.

## Usage Examples

### Converting Dictionary to Tuple List
```python
from yi import kv_tuple_list

d = {'apple': 1, 'banana': 2}
tuple_list = kv_tuple_list(d)
print(tuple_list)  # Output: [('apple', 1), ('banana', 2)]
```

### Displaying Dictionary as Table String
```python
from yi import table_str_with_key_and_value_columns

d = {'id': 1, 'name': 'John Doe'}
table_str = table_str_with_key_and_value_columns(d)
print(table_str)
```

### Creating a Namedtuple from Dictionary
```python
from yi import namedtuple

d = {'x': 1, 'y': 2}
Point = namedtuple(d, name='Point')
point = Point(x=1, y=2)
print(point.x, point.y)  # Output: 1 2
```

### Using Hashable Dictionary
```python
from yi import hashabledict

hd = hashabledict({'apple': 1, 'banana': 2})
dictionary_set = {hd}
print(dictionary_set)  # Output: {hashabledict({'apple': 1, 'banana': 2})}
```

### Inverting Dictionary Mappings
```python
from yi import inverse_one_to_one, inverse_one_to_many, inverse_many_to_one

# One-to-one inversion
d = {'A': 'a', 'B': 'b'}
print(inverse_one_to_one(d))  # Output: {'a': 'A', 'b': 'B'}

# One-to-many inversion
d = {'A': ['a', 'aa'], 'B': ['b']}
print(inverse_one_to_many(d))  # Output: {'a': 'A', 'aa': 'A', 'b': 'B'}

# Many-to-one inversion
d = {'a': 'A', 'aa': 'A', 'b': 'B'}
print(inverse_many_to_one(d))  # Output: {'A': ['a', 'aa'], 'B': ['b']}
```

### Word Replacement in Text
```python
from yi import word_replacer

rep_dict = {'hello': 'hi', 'world': 'earth'}
replace = word_replacer(rep_dict)
text = "hello world"
print(replace(text))  # Output: hi earth
```

## Documentation
Each function and class in the `yi` package is documented with docstrings, providing examples and detailed usage instructions. Users are encouraged to refer to the source code for additional details on the functionality and to explore the wide range of utilities offered by the package.
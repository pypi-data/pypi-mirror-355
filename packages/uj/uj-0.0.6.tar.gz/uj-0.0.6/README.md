# uj
Utils to work with lists

To install:	```pip install uj```

## Overview
The `uj` package provides a set of utilities designed to assist with list operations, particularly focusing on operations that involve numerical data and set-like behavior with performance optimizations. Key functionalities include maintaining lists of maximum or minimum items, checking membership, sorting, and various utility functions to handle list and non-list data seamlessly.

## Features

### KeepMaxK
A class that maintains a list of the k largest items seen so far.

#### Usage:
```python
from uj import KeepMaxK

max_k = KeepMaxK(3)
max_k.push(10)
max_k.push(20)
max_k.push(5)
max_k.push(15)
print(max_k)  # Output will be the 3 largest values [10, 20, 15]
```

### KeepMinK
Similar to `KeepMaxK`, but maintains a list of the k smallest items. It only works with items that are pairs (tuples of two elements).

#### Usage:
```python
from uj import KeepMinK

min_k = KeepMinK(2)
min_k.push((10, 'a'))
min_k.push((20, 'b'))
min_k.push((5, 'c'))
print(min_k.get_list())  # Output will be [(5, 'c'), (10, 'a')]
```

### KeepMaxUnikK
Maintains a list of the k largest unique items, where uniqueness is determined by the item, not the value.

#### Usage:
```python
from uj import KeepMaxUnikK

max_unik_k = KeepMaxUnikK(2)
max_unik_k.push('apple', 10)
max_unik_k.push('banana', 20)
max_unik_k.push('apple', 15)
print(max_unik_k.items_sorted())  # Output will be ['banana', 'apple']
```

### Utility Functions

#### `first_non_zero`
Finds the first non-zero element in an array.

#### Usage:
```python
from uj import first_non_zero

print(first_non_zero([0, 0, 2, 0]))  # Output: 2
```

#### `first_true_cond`
Returns the index of the first element for which a condition is True.

#### Usage:
```python
from uj import first_true_cond

print(first_true_cond(lambda x: x > 5, [1, 4, 6, 8]))  # Output: 2
```

#### `ismember_lidx`
Determines if elements of list A are in list B and returns a list of booleans.

#### Usage:
```python
from uj import ismember_lidx

print(ismember_lidx([1, 2, 3], [3, 4, 5]))  # Output: [False, False, True]
```

#### `sort_as`
Sorts one list based on the sorting of another list.

#### Usage:
```python
from uj import sort_as

print(sort_as([1, 2, 3], [3, 1, 2]))  # Output: [2, 3, 1]
```

#### `all_true` and `any_true`
Check if all or any entries in a list are True respectively.

#### Usage:
```python
from uj import all_true, any_true

print(all_true([True, False, True]))  # Output: False
print(any_true([True, False, False]))  # Output: True
```

#### `to_str`
Converts a list to a string with a specified separator.

#### Usage:
```python
from uj import to_str

print(to_str([1, 2, 3], sep='-'))  # Output: '1-2-3'
```

#### `ascertain_list`
Ensures the input is returned as a list, useful for single elements or non-list iterables.

#### Usage:
```python
from uj import ascertain_list

print(ascertain_list('hello'))  # Output: ['hello']
print(ascertain_list([1, 2, 3]))  # Output: [1, 2, 3]
```

These utilities are designed to simplify and optimize operations that are commonly needed when dealing with lists and arrays in Python, particularly in data processing and computational tasks.
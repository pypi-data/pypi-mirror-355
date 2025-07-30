# kc
Utils for filtering

To install:	```pip install kc```

## Overview

The `kc` package provides utility functions for creating filters that can be applied to data collections in Python. These filters allow for inclusion or exclusion of elements based on specified criteria. The package is particularly useful for filtering lists, tuples, or other iterable collections based on dynamic conditions.

## Main Functions

### mk_inclusion_exclusion_filter

This function creates a filter based on both inclusion and exclusion criteria. It returns a filter function that can be used with Python's built-in `filter()` function.

- **Parameters:**
  - `include`: List-like collection of elements to include.
  - `exclude`: List-like collection of elements to exclude.
  - `key`: A function or a key to apply to elements of the iterable for comparison.

- **Usage Example:**

  ```python
  # Inclusion only
  filt = mk_inclusion_exclusion_filter(include=[2, 4])
  print(list(filter(filt, [1, 2, 3, 4, 5])))

  # Exclusion only
  filt = mk_inclusion_exclusion_filter(exclude=[2, 4])
  print(list(filter(filt, [1, 2, 3, 4, 5])))

  # Inclusion and Exclusion
  filt = mk_inclusion_exclusion_filter(include=[1, 2, 3, 4], exclude=[1, 3])
  print(list(filter(filt, [1, 2, 3, 4, 5])))
  ```

### mk_inclusion_filter

Creates a filter that includes elements if they are in the specified `include` list.

- **Parameters:**
  - `include`: List-like collection of elements to include.
  - `key`: A function or a key to apply to elements of the iterable for comparison.

- **Usage Example:**

  ```python
  filt = mk_inclusion_filter(include=[2, 4])
  print(list(filter(filt, [1, 2, 3, 4, 5])))
  ```

### mk_exclusion_filter

Creates a filter that excludes elements if they are in the specified `exclude` list.

- **Parameters:**
  - `exclude`: List-like collection of elements to exclude.
  - `key`: A function or a key to apply to elements of the iterable for comparison.

- **Usage Example:**

  ```python
  filt = mk_exclusion_filter(exclude=[2, 4])
  print(list(filter(filt, [1, 2, 3, 4, 5])))
  ```

## Installation

To install the `kc` package, use the following command:

```bash
pip install kc
```

## Contributing

Contributions to the `kc` package are welcome. Please ensure that any pull requests or issues are clear and provide sufficient information for review.
# ke
File access utils

To install:	```pip install ke```

## Overview
The `ke` package provides a comprehensive set of utilities for file access and manipulation, designed to simplify the process of reading, writing, and managing files both locally and on Amazon S3. It abstracts file paths and extensions handling, supports environment-based configurations, and integrates seamlessly with pandas for data handling.

## Features
- **Local and S3 File Access**: Simplify file operations in local filesystems and Amazon S3.
- **Environment Variable Integration**: Use environment variables to manage file paths dynamically.
- **Extension Handling**: Automatically manage file extensions when accessing files.
- **Read and Write Operations**: Facilitate common file operations such as read, write, and append, with special handling for text and binary data.
- **Data Serialization**: Utilize pickle for object serialization and deserialization.
- **Pandas Integration**: Special methods to handle pandas objects effectively when loading from or saving to files.

## Usage Examples

### Basic File Access
To create a file accessor for local files:
```python
from ke import for_local

# Create a file accessor for local files in the default root directory
local_accessor = for_local()

# Save a string to a file
local_accessor.save("Hello, World!", "hello.txt")

# Load a string from a file
content = local_accessor.load("hello.txt")
print(content)
```

### Accessing Files on Amazon S3
To handle files on Amazon S3:
```python
from ke import for_s3

# Create a file accessor for S3 with a specific relative root
s3_accessor = for_s3(relative_root='my/data/folder')

# Save data to a file on S3
s3_accessor.save("Data to save", "data.txt")

# Load data from a file on S3
data = s3_accessor.load("data.txt")
print(data)
```

### Using Environment Variables
To use an environment variable for the root folder:
```python
import os
from ke import for_local

# Assume 'MY_DATA_PATH' is an environment variable set to the data directory path
os.environ['MY_DATA_PATH'] = '/path/to/data'

# Create a file accessor that uses this environment variable
data_accessor = for_local(root_folder=os.environ['MY_DATA_PATH'])

# Work with files in the specified directory
data_accessor.save("Sample data", "sample.txt")
```

### Working with Pandas
To save and load pandas DataFrames:
```python
import pandas as pd
from ke import for_local

# Create a DataFrame
df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

# Create a local file accessor
local_accessor = for_local()

# Save DataFrame to a pickle file
local_accessor.save(df, "dataframe.pkl")

# Load DataFrame from a pickle file
loaded_df = local_accessor.load("dataframe.pkl")
print(loaded_df)
```

## Classes and Methods
- `Accessor`: The main class used for creating file accessors. It handles the creation of file paths, loading, and saving of files.
- `for_local()`: Factory function to create an `Accessor` for local file operations.
- `for_s3()`: Factory function to create an `Accessor` for Amazon S3 file operations.
- `ms_data_path()`: Utility function to construct a full path given a relative root, based on a predefined or environment-specified base directory.

## Installation
To install the package, use pip:
```bash
pip install ke
```

For more details on the implementation and additional functionalities, refer to the source code documentation within the package.
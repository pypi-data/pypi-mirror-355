# csvvv

> **Warning:** This project is for **cybersecurity demonstration purposes only**. It may contain potential security vulnerabilities, and it should **not** be used in production environments.

## Features

- **Sniff CSV file structure**: Attempts to detect delimiters, quote characters, and more.
- **Read CSV as dictionaries**: Implements `DictReader` for reading CSV files as Python dictionaries.
- **Write CSV from dictionaries**: Implements `DictWriter` to write dictionaries as CSV files.

## Security Disclaimer

This package **may contain vulnerabilities** that could lead to unintended behavior or security issues.
Please **do not use this package** in real-world applications where security and data integrity are important.

## Installation

This package can be installed via pip:
```python
pip install csvvv
```

## Usage

```python
from csvvv import DictReader, DictWriter, Sniffer

# Reading CSV as dictionaries
with open('data.csv', 'r') as f:
    reader = DictReader(f)
    for row in reader:
        print(row)

# Writing CSV from dictionaries
with open('output.csv', 'w') as f:
    writer = DictWriter(f, fieldnames=["name", "age"])
    writer.writeheader()
    writer.writerow({"name": "Charlie", "age": 40})
```
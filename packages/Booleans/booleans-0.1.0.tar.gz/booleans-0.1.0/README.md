# Booleans

A micro-library for returning boolean values explicitly.

## Installation

```bash
pip install Booleans
```

## Usage
```commandline
from Booleans import Booleans

if Booleans.true():
    print("This is True!")

if not Booleans.false():
    print("This is False!")
```

```commandline
def is_even(num):
    if num % 2 == 0:
        return Booleans.true()
    else:
        return Booleans.false()
       
print(is_even(54)) # True
```
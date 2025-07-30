# Progbarr

[![PyPI - Version](https://img.shields.io/pypi/v/progbarr)](https://pypi.org/project/progbarr/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/progbarr)](https://pypi.org/project/progbarr/)
[![License](https://img.shields.io/pypi/l/progbarr)](https://github.com/haripowesleyt/progbarr/blob/main/LICENSE)
[![Python Versions](https://img.shields.io/pypi/pyversions/progbarr)](https://pypi.org/project/progbarr/)

Progbarr is a Python library for creating highly performant and customizable progress bars in the console.

## Features

- Supports filling with **any UNICODE character**
- Supports setting foreground & background **colors**
    - by [**name**](https://htmlcolorcodes.com/color-names/) (e.g., `green`),
    - by **HEX** (e.g., `#ff00ff`), or
    - by **RGB** (e.g., `128,0,128`)
- Minimal performance overhead

## Installation

```bash
pip install progbarr
```

## Usage

### Syntax

```python
from progbarr import ProgressBar

with ProgressBar(message, tasks, length, chars, color, bgcolor) as pb:
    for _ in range(tasks):
      # Perform some task
      pb.advance()
```

The table below explains the constructor parameters:

| Parameter | Type           | Description         | Tip                                   |
|-----------|----------------|---------------------|---------------------------------------|
| `message` | `str`          | What is being done? | Use present participle form           |
| `tasks`   | `int`          | Number of tasks     | Must equal loop iterations            |
| `length`  | `int`          | Bar length          | Must be a factor of `tasks`           |
| `chars`   | `str`          | Bar characters      | border + fill + head + empty + border |
| `color`   | `str` / `None` | Foreground color    | Use `None` for terminal default       |
| `bgcolor` | `str` / `None` | Background color    | Use `None` for terminal default       |

### Example (Classic)

```python
from time import sleep
from progbarr import ProgressBar

with ProgressBar("Sleeping", 20, 20, "[## ]", None, None) as pb:
    for _ in range(20):
        sleep(0.35)
        pb.advance()
```

![example-classic](https://raw.githubusercontent.com/haripowesleyt/progbarr/main/assets/images/example-classic.gif)

### More Examples

**NB:** The following example progress bars simulate the same tasks as the classic example above.

#### 1. Block

```python
with ProgressBar("Sleeping", 20, 20, "│   │", None, "orange") as pb: ...
```

![example-block](https://raw.githubusercontent.com/haripowesleyt/progbarr/main/assets/images/example-block.gif)

#### 2. Circles

```python
with ProgressBar("Sleeping", 20, 20, " ●●○ ", "crimson", None) as pb: ...
```
![example-circles](https://raw.githubusercontent.com/haripowesleyt/progbarr/main/assets/images/example-circles.gif)

#### 3. Squares

```python
with ProgressBar("Sleeping", 20, 20, " ◼◼◻ ", "teal", None) as pb: ...
```

![example-square](https://raw.githubusercontent.com/haripowesleyt/progbarr/main/assets/images/example-squares.gif)

#### 4. Track

```python
with ProgressBar("Sleeping", 20, 20, " ―⚈― ", "darkgrey", None) as pb: ...
```

![example-track](https://raw.githubusercontent.com/haripowesleyt/progbarr/main/assets/images/example-track.gif)

## License

This project is licensed under the **MIT License** – see the [LICENSE](https://raw.githubusercontent.com/haripowesleyt/progbarr/main/LICENSE) file for details.
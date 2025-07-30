# sysmess

Fancy terminal message box renderer using Unicode box characters and ANSI styling.

## Installation & Building

  ### Install Via PIP (Recomended)
    - `pip install sysmess`

  ### Build From Source
  - Clone the repository `git clone https://github.com/canadaluke888/sysmess.git`

  - Build the extension in-place:

    ```bash
    python3 setup.py build
    ```

  - (Optional) Install into your current environment:
  
    - Create a virtual environment: `python3 -m venv .venv` (MacOS & Linux) | `python -m venv .venv` (Windows)

    - Activate virtual environment: `source .venv/bin/activate` (MacOS & Linux) | `.venv/Scripts/Activate` (Windows)

    - Install into current environment:

        ```bash
        pip install .
        ```

## Usage

```python
import sysmess

msg = sysmess.fancy_box(
    "Hello, world!",
    title="Greeting",
    center=True,
    bold=True,
    italic=False,
)
print(msg)

# Measure the width of the box (including borders)
width = sysmess.measure_box_width("Hello, world!", title="Greeting")
print(width)
```

You can also specify colors for the border, title, and body:

```python
msg = sysmess.fancy_box(
    "Colored message",
    title="Colorful",
    border_color="magenta",
    title_color="cyan",
    body_color="yellow"
)
print(msg)
```

Supported color names: black, red, green, yellow, blue, magenta, cyan, white,
bright_black, bright_red, bright_green, bright_yellow, bright_blue,
bright_magenta, bright_cyan, bright_white.

## Examples

Once built (or installed), run the demonstration script to see sample outputs:

```bash
python3 examples.py
```

## Testing

Run the unit tests using the included test runner:

```bash
python3 test.py
```

## Continuous Integration

A GitHub Actions workflow is included at `.github/workflows/ci.yml`, which builds the extension, runs the tests, and executes the examples on each push or pull request to `main`.


# Lambda Explorer

A small GUI application for interacting with symbolic formulas and plotting them using [Dear PyGui](https://github.com/hoffstadt/dearpygui).

The GUI presents every available formula and lets you calculate or plot results
by filling in all but one variable. Formulas are defined with
[SymPy](https://www.sympy.org/) and are automatically discovered when the
application starts.
Displayed formulas are rendered from LaTeX using Matplotlib for clarity.

## Installation

```bash
pip install lambda-explorer
```

To install from source:

```bash
pip install -r requirements.txt
pip install -e .
```

## Usage

After installation you can launch the GUI with the command:

```bash
lambda-explorer
```

This will open the formula browser where you can calculate and visualize formulas.

### Lightweight CLI

If memory usage is a concern you can use a simple command line interface:

```bash
lambda-explorer-cli
```

This avoids the GUI and only loads the selected formula when needed.

## Library Usage

`lambda-explorer` can also be used programmatically. Formula classes are
available in `lambda_explorer.tools.aero_formulas` and provide a convenient
`solve()` method. Exactly one variable must be omitted so that it can be
calculated:

```python
from lambda_explorer.tools.aero_formulas import ReynoldsNumber

eq = ReynoldsNumber()
# Solve for Re while providing the other values
re = eq.solve(rho=1.225, V=50.0, c=0.5, mu=1.8e-5)
print(re)
```

To launch the GUI from Python simply call `lambda_explorer.main()`:

```python
from lambda_explorer import main

main()
```

Default values used inside the GUI can be customised. Use the *Defaults* tab in
any formula window to load or save the `defaults.yaml` file directly, or choose
"Save As" to export the defaults to a custom YAML file. The defaults map
variable names to their stored string values.

The application also remembers your window layout. When you close the GUI, the
current positions and sizes of all windows are written to `layout.ini` and the
list of visible windows is stored in `open_windows.json`. Both the layout and
open windows are restored on the next start.

The *Settings* window lets you adjust the logging level of the application at
runtime. Choose between `DEBUG`, `INFO`, `WARNING` and `ERROR` to control the
amount of information written to the log window.

## Developer Documentation

Developers who want to implement additional formulas can follow the guide in
[`docs/developer_guide.md`](docs/developer_guide.md). It describes the required
class structure and how new equations are automatically integrated into the GUI.

## Development Workflow

Use the provided `Makefile` to streamline common tasks:

```bash
make install  # install dependencies and project in editable mode
make format   # apply code formatting using Black
make lint     # run pre-commit hooks
```

Run `make run` to start the GUI or `make run-cli` for the command line interface.

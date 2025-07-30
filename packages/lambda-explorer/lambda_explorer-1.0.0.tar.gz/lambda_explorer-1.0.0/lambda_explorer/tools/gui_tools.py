# gui_tools.py
import sympy  # type: ignore
from typing import Dict, Type, Optional, List
import logging
from pathlib import Path
import csv
import coloredlogs
import dearpygui.dearpygui as dpg
import matplotlib
from matplotlib.backends.backend_agg import FigureCanvasAgg

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from .. import logger, log_calls

# path to application icons
ICON_PATH = Path(__file__).resolve().parent.parent / "logo" / "favicon.ico"

# Load formula classes
from .aero_formulas import ReynoldsNumber, DynamicViscosity, KinematicViscosity
from .interpolation_formula import ExampleIcingEquation
from .formula_base import Formula
from .formula_registry import formula_registry
from .solver import FormulaSolver
from .default_manager import default_values, load_defaults_file, save_defaults_file
from .layout_manager import load_layout, save_layout, LAYOUT_FILE
from .window_state_manager import load_open_windows, save_open_windows


# Use a central registry to manage available formulas
formula_classes = formula_registry.formula_classes
custom_formula_classes = formula_registry.custom_formula_classes

# simple helper for cascading window placement
_next_pos = [20, 20]
_offset = 30


@log_calls
def _get_next_pos() -> List[int]:
    pos = _next_pos.copy()
    _next_pos[0] += _offset
    _next_pos[1] += _offset
    logger.debug("Next window position: %s", pos)
    return pos


@log_calls
def create_latex_texture(latex: str) -> str:
    """Render LaTeX text to a Dear PyGui texture.

    The canvas width was increased to prevent long formulas from being cut off.
    """
    fig, ax = plt.subplots(figsize=(3.0, 1.0), dpi=300)
    fig.patch.set_alpha(0.0)
    ax.axis("off")
    text = ax.text(0.0, 0.0, f"${latex}$", color="white", ha="left", va="bottom")

    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    renderer = canvas.get_renderer()
    bbox = text.get_window_extent(renderer)

    buf = np.asarray(canvas.buffer_rgba(), dtype=np.float32)
    h_total, w_total = buf.shape[0], buf.shape[1]
    pad = 2
    top = max(int(h_total - bbox.y1) - pad, 0)
    bottom = min(int(h_total - bbox.y0) + pad, h_total)
    left = max(int(bbox.x0) - pad, 0)
    right = min(int(bbox.x1) + pad, w_total)
    buf = buf[top:bottom, left:right, :]
    buffer = buf / 255.0
    width, height = buffer.shape[1], buffer.shape[0]

    tag = f"tex_{dpg.generate_uuid()}"
    with dpg.texture_registry(show=False):
        dpg.add_raw_texture(
            width, height, buffer, tag=tag, format=dpg.mvFormat_Float_rgba
        )
    plt.close(fig)
    return tag


# Default values storage
for cls in formula_classes.values():
    for var in getattr(cls, "variables", []):
        default_values.setdefault(var, "")
load_defaults_file()

# Mapping of log level names to Dear PyGui colours
LOG_COLORS = {
    "DEBUG": [150, 150, 150, 255],
    "VERBOSE": [180, 180, 180, 255],
    "INFO": [255, 255, 255, 255],
    "WARNING": [255, 255, 0, 255],
    "ERROR": [255, 0, 0, 255],
    "CRITICAL": [255, 0, 0, 255],
}


class GuiLogHandler(logging.Handler):
    """Logging handler that writes coloured records to a Dear PyGui window."""

    @log_calls
    def __init__(self, target: str) -> None:
        super().__init__()
        self.target = target

    @log_calls
    def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - GUI
        msg = self.format(record)
        color = LOG_COLORS.get(record.levelname, [255, 255, 255, 255])
        dpg.add_text(msg, parent=self.target, color=color)


log_window_tag = "logger_window"
log_container_tag = "logger_container"
gui_log_handler: Optional[GuiLogHandler] = None

settings_window_tag = "settings_window"
log_level_tag = "log_level_combo"
log_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]


@log_calls
def setup_logger_window() -> None:  # pragma: no cover - GUI
    """Create the logging window and attach handler."""
    global gui_log_handler
    if gui_log_handler:
        return
    with dpg.window(
        label="Logs", tag=log_window_tag, width=400, height=200, show=False
    ):
        with dpg.child_window(tag=log_container_tag, autosize_x=True, autosize_y=True):
            pass
    gui_log_handler = GuiLogHandler(log_container_tag)
    gui_log_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(gui_log_handler)


@log_calls
def show_log_window(
    sender=None, app_data=None, user_data=None
):  # pragma: no cover - GUI
    """Display the logging window."""
    setup_logger_window()
    logger.debug("Showing log window")
    dpg.show_item(log_window_tag)


@log_calls
def set_log_level_callback(sender, app_data, user_data):  # pragma: no cover - GUI
    """Update the global logging level from the settings window."""
    level = str(app_data)
    # Newer versions of ``coloredlogs`` no longer accept the ``logger``
    # keyword argument in :func:`set_level`. Set the level on the root
    # handler directly to avoid compatibility issues.
    coloredlogs.set_level(level)
    logger.setLevel(level)
    logger.info("Logging level changed to %s", level)


@log_calls
def show_settings_window(
    sender=None, app_data=None, user_data=None
):  # pragma: no cover - GUI
    """Display the settings window allowing adjustment of options."""
    logger.debug("Showing settings window")
    if not dpg.does_item_exist(settings_window_tag):
        with dpg.window(
            label="Settings",
            tag=settings_window_tag,
            width=220,
            height=90,
            pos=_get_next_pos(),
            show=False,
        ):
            dpg.add_combo(
                log_levels,
                label="Log Level",
                default_value=logging.getLevelName(logger.level),
                tag=log_level_tag,
                callback=set_log_level_callback,
            )
    dpg.show_item(settings_window_tag)


@log_calls
def _add_formula_to_overview(name: str) -> None:
    """Insert a formula entry into the overview window."""
    item_tag = f"item_{name}"
    dpg.add_text(name, tag=item_tag, parent="main_window")
    with dpg.item_handler_registry() as handler:
        dpg.add_item_clicked_handler(callback=open_formula_window, user_data=name)
    dpg.bind_item_handler_registry(item_tag, handler)


@log_calls
def _create_formula_callback(sender, app_data, user_data):
    """Create a custom formula from editor inputs."""
    name = dpg.get_value(user_data["name"]).strip()
    vars_raw = dpg.get_value(user_data["vars"])
    expr_text = dpg.get_value(user_data["expr"])
    delete_combo = user_data["delete_combo"]
    if not name or not vars_raw or not expr_text:
        logger.error("All fields must be filled")
        return
    if name in formula_classes:
        logger.error("Formula %s already exists", name)
        return
    var_names = [v.strip() for v in vars_raw.split(",") if v.strip()]
    symbols = sympy.symbols(" ".join(var_names))
    sym_dict = dict(zip(var_names, symbols))
    try:
        expr = sympy.sympify(expr_text, locals=sym_dict)
    except Exception as exc:
        logger.error("Invalid expression: %s", exc)
        return
    eq = sympy.Eq(sym_dict[var_names[0]], expr)
    cls = formula_registry.create_formula(name, var_names, eq)
    for v in var_names:
        default_values.setdefault(v, "")
    _add_formula_to_overview(name)
    dpg.configure_item(delete_combo, items=list(custom_formula_classes))
    logger.info("Added custom formula %s", name)


@log_calls
def _delete_formula_callback(sender, app_data, user_data):
    """Remove a custom formula and its window."""
    combo_tag = user_data
    name = dpg.get_value(combo_tag)
    if not name:
        return
    if name not in custom_formula_classes:
        return
    formula_registry.delete_formula(name)
    window_tag = f"win_{name}"
    item_tag = f"item_{name}"
    if dpg.does_item_exist(window_tag):
        dpg.delete_item(window_tag)
    if dpg.does_item_exist(item_tag):
        dpg.delete_item(item_tag)
    dpg.configure_item(combo_tag, items=list(custom_formula_classes))
    logger.info("Deleted custom formula %s", name)


@log_calls
def show_formula_editor(sender=None, app_data=None, user_data=None):
    """Display the formula editor window."""
    tag = "formula_editor"
    if dpg.does_item_exist(tag):
        dpg.show_item(tag)
        return
    with dpg.window(
        label="Formula Editor", tag=tag, width=400, height=220, pos=_get_next_pos()
    ):
        name_tag = "fe_name"
        vars_tag = "fe_vars"
        expr_tag = "fe_expr"
        delete_combo = "fe_delete"
        dpg.add_input_text(label="Name", tag=name_tag)
        dpg.add_input_text(label="Variables", tag=vars_tag, hint="comma separated")
        dpg.add_input_text(label="Expression", tag=expr_tag, hint="for first variable")
        dpg.add_button(
            label="Add",
            callback=_create_formula_callback,
            user_data={
                "name": name_tag,
                "vars": vars_tag,
                "expr": expr_tag,
                "delete_combo": delete_combo,
            },
        )
        dpg.add_separator()
        dpg.add_combo(list(custom_formula_classes), label="Delete", tag=delete_combo)
        dpg.add_button(
            label="Delete", callback=_delete_formula_callback, user_data=delete_combo
        )
    dpg.show_item(tag)


# Callback: calculate just-cleared input and then full calculation
@log_calls
def calc_input_callback(sender, app_data, user_data):
    """Clear the input field and immediately recalculate the equation."""
    input_tag = user_data["input_tag"]
    logger.debug("Calc input callback for %s", input_tag)
    dpg.set_value(input_tag, "")
    calculate_callback(sender, app_data, user_data)


# Callback to set default into input
@log_calls
def set_default_callback(sender, app_data, user_data):
    """Insert the stored default value for the given variable."""
    input_tag, var = user_data
    logger.debug("Setting default for %s", var)
    default = default_values.get(var, "")
    dpg.set_value(input_tag, default)


# Callback to store the current input as default
@log_calls
def pull_default_callback(sender, app_data, user_data):
    """Save the value from the input field as the new default."""
    input_tag, var = user_data
    value = str(dpg.get_value(input_tag))
    default_values[var] = value
    logger.debug("Stored default for %s: %s", var, value)


# Callback to calculate formula from bottom button
@log_calls
def calculate_callback(sender, app_data, user_data):
    """Solve the equation with the values entered by the user."""
    solver: FormulaSolver = user_data["solver"]
    eq = solver.formula
    vars_tags = user_data["vars_tags"]
    error_tag = user_data["error_tag"]
    logger.debug("Calculate callback triggered for %s", eq.__class__.__name__)
    dpg.set_value(error_tag, "")
    knowns: Dict[str, float] = {}
    missing = []
    for var, tag in vars_tags.items():
        val = dpg.get_value(tag)
        if not str(val).strip():
            missing.append(var)
        else:
            try:
                knowns[var] = float(val)
            except ValueError:
                dpg.set_value(error_tag, f"Invalid value for {var}: '{val}'")
                return
    if len(missing) != 1:
        dpg.set_value(
            error_tag,
            f"Please leave exactly one variable empty (currently {len(missing)})",
        )
        return
    try:
        result = solver.solve(knowns)
        logger.info("Solved %s for %s", eq.__class__.__name__, missing[0])
        dpg.set_value(vars_tags[missing[0]], str(result))
    except Exception as e:
        logger.error("Error solving %s: %s", eq.__class__.__name__, e)
        dpg.set_value(error_tag, str(e))


# Helper to update constant input fields for plotting
@log_calls
def update_plot_inputs(sender, app_data, user_data):
    """Refresh the constant value input fields when plot variables change."""
    solver: FormulaSolver = user_data["solver"]
    eq = solver.formula
    logger.debug("Update plot inputs for %s", eq.__class__.__name__)
    x_var = dpg.get_value(user_data["x_var_tag"])
    y_var = dpg.get_value(user_data["y_var_tag"])
    group = user_data["const_group"]
    dpg.delete_item(group, children_only=True)
    user_data["const_tags"].clear()
    for var in eq.vars:
        if var in (x_var, y_var):
            continue
        tag = f"{group}_{var}"
        default = default_values.get(var, "")
        dpg.add_input_text(parent=group, label=var, tag=tag, default_value=default)
        user_data["const_tags"][var] = tag


# Callback to compute and display plot data
@log_calls
def plot_callback(sender, app_data, user_data):
    """Calculate plot data for the selected x/y variables."""
    solver: FormulaSolver = user_data["solver"]
    eq = solver.formula
    logger.debug("Plot callback for %s", eq.__class__.__name__)
    x_var = dpg.get_value(user_data["x_var_tag"])
    y_var = dpg.get_value(user_data["y_var_tag"])
    logger.debug("Plotting %s vs %s", y_var, x_var)
    start = float(dpg.get_value(user_data["x_start"]))
    end = float(dpg.get_value(user_data["x_end"]))
    step = float(dpg.get_value(user_data["x_step"]))

    if step <= 0:
        logger.error("Step must be positive, got %s", step)
        return

    max_points = 10000
    num_points = int(max(0, (end - start) / step)) + 1
    if num_points > max_points:
        logger.warning(
            "Requested %d points exceeds limit of %d; truncating",
            num_points,
            max_points,
        )
        end = start + step * (max_points - 1)
        num_points = max_points
    consts = {}
    for var, tag in user_data["const_tags"].items():
        val = dpg.get_value(tag)
        try:
            consts[var] = float(val)
        except ValueError:
            return
    xs: List[float] = []
    ys: List[float] = []
    x = start
    for _ in range(num_points):
        knowns = consts.copy()
        knowns[x_var] = x
        try:
            y_val = solver.solve(knowns)
        except Exception:
            break
        xs.append(x)
        ys.append(y_val)
        x += step
    dpg.set_value(user_data["series_tag"], [xs, ys])
    logger.info("Plotted %d points", len(xs))
    if xs and ys:
        max_idx = ys.index(max(ys))
        if dpg.does_item_exist(user_data["annotation_tag"]):
            dpg.delete_item(user_data["annotation_tag"])
        # Ensure the annotation is attached directly to the plot. Some versions
        # of DearPyGui may return an error if the stored parent is not a plot,
        # so verify and correct the parent before adding the annotation.
        plot_tag = user_data["plot_tag"]
        if dpg.get_item_type(plot_tag) != dpg.mvPlot:
            # fall back to using the parent of the Y axis (which is the plot)
            plot_tag = dpg.get_item_parent(user_data["axis_y_tag"])
        dpg.add_plot_annotation(
            parent=plot_tag,
            tag=user_data["annotation_tag"],
            default_value=(xs[max_idx], ys[max_idx]),
            label=f"max={ys[max_idx]:.2f}",
        )


@log_calls
def export_csv_callback(sender, app_data, user_data):
    """Export the plotted data to a CSV file."""
    path = app_data.get("file_path_name") if isinstance(app_data, dict) else None
    logger.debug("Export CSV requested: %s", path)
    xs, ys = dpg.get_value(user_data["series_tag"])
    if not path:
        logger.warning("No file selected for CSV export")
        return
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["x", "y"])
            for x, y in zip(xs, ys):
                writer.writerow([x, y])
        logger.info("Exported CSV to %s", path)
    except OSError as exc:
        logger.error("Failed to export CSV: %s", exc)


@log_calls
def save_defaults_callback(sender, app_data, user_data):
    """Save edited defaults from the defaults tab."""
    logger.debug("Saving defaults from UI")
    for var, tag in user_data.items():
        default_values[var] = dpg.get_value(tag)


@log_calls
def export_defaults_callback(sender, app_data, user_data):
    path = app_data.get("file_path_name") if isinstance(app_data, dict) else None
    logger.debug("Export defaults to %s", path)
    if not path:
        return
    save_defaults_callback(sender, app_data, user_data)
    save_defaults_file(path)


@log_calls
def import_defaults_callback(sender, app_data, user_data):
    path = app_data.get("file_path_name") if isinstance(app_data, dict) else None
    logger.debug("Import defaults from %s", path)
    if not path:
        return
    load_defaults_file(path)
    for var, tag in user_data.items():
        if var in default_values:
            dpg.set_value(tag, default_values[var])


@log_calls
def export_defaults_default(sender, app_data, user_data):
    """Export defaults to the standard ``defaults.yaml`` file."""
    logger.debug("Exporting defaults to defaults.yaml")
    save_defaults_callback(sender, app_data, user_data)
    save_defaults_file("defaults.yaml")


@log_calls
def import_defaults_default(sender, app_data, user_data):
    """Load defaults from the standard ``defaults.yaml`` file."""
    logger.debug("Importing defaults from defaults.yaml")
    load_defaults_file("defaults.yaml")
    for var, tag in user_data.items():
        if var in default_values:
            dpg.set_value(tag, default_values[var])


# Open per-formula window
@log_calls
def open_formula_window(sender, app_data, user_data):
    """Create or show a window for the selected formula."""
    cls_name = user_data
    logger.info("Open formula window: %s", cls_name)
    logger.debug("Creating solver and window for %s", cls_name)
    eq = formula_classes[cls_name]()
    solver = FormulaSolver(eq)
    window_tag = f"win_{cls_name}"
    if dpg.does_item_exist(window_tag):
        dpg.show_item(window_tag)
        return
    vars_tags: Dict[str, str] = {}
    error_tag = f"{window_tag}_error"
    shared_data = {
        "equation": eq,
        "vars_tags": vars_tags,
        "error_tag": error_tag,
        "solver": solver,
    }

    plot_data = {
        "equation": eq,
        "const_tags": {},
        "solver": solver,
    }

    with dpg.window(
        label=cls_name, tag=window_tag, width=450, height=400, pos=_get_next_pos()
    ):
        dpg.add_text(f"Formula: {cls_name}")
        tex_tag = create_latex_texture(sympy.latex(eq.eq))
        dpg.add_image(tex_tag)
        with dpg.tab_bar():
            with dpg.tab(label="Calculation"):
                for var in eq.vars:
                    input_tag = f"{window_tag}_input_{var}"
                    default = default_values.get(var, "")
                    with dpg.group(horizontal=True):
                        dpg.add_input_text(
                            tag=input_tag, label=var, default_value=default
                        )
                        shared_data["input_tag"] = input_tag
                        dpg.add_button(
                            label="Calc",
                            callback=calc_input_callback,
                            user_data=shared_data.copy(),
                        )
                        dpg.add_button(
                            label="Default",
                            callback=set_default_callback,
                            user_data=(input_tag, var),
                        )
                        dpg.add_button(
                            label="Set Default",
                            callback=pull_default_callback,
                            user_data=(input_tag, var),
                        )
                    vars_tags[var] = input_tag
                dpg.add_text(tag=error_tag, default_value="", color=[255, 0, 0])
                dpg.add_button(
                    label="Calculate",
                    callback=calculate_callback,
                    user_data=shared_data,
                )

            with dpg.tab(label="Plot"):
                x_var_tag = f"{window_tag}_xvar"
                y_var_tag = f"{window_tag}_yvar"
                x_start_tag = f"{window_tag}_xstart"
                x_end_tag = f"{window_tag}_xend"
                x_step_tag = f"{window_tag}_xstep"
                const_group_tag = f"{window_tag}_const"
                plot_series_tag = f"{window_tag}_series"
                axis_y_tag = f"{window_tag}_yaxis"
                annotation_tag = f"{window_tag}_annotation"
                plot_tag = f"{window_tag}_plot"

                plot_data.update(
                    {
                        "x_var_tag": x_var_tag,
                        "y_var_tag": y_var_tag,
                        "x_start": x_start_tag,
                        "x_end": x_end_tag,
                        "x_step": x_step_tag,
                        "const_group": const_group_tag,
                        "series_tag": plot_series_tag,
                        "axis_y_tag": axis_y_tag,
                        "annotation_tag": annotation_tag,
                        "plot_tag": plot_tag,
                    }
                )

                var_names = list(eq.vars)
                dpg.add_combo(
                    var_names,
                    default_value=var_names[0],
                    label="X",
                    tag=x_var_tag,
                    callback=update_plot_inputs,
                    user_data=plot_data,
                )
                dpg.add_combo(
                    var_names,
                    default_value=var_names[1] if len(var_names) > 1 else var_names[0],
                    label="Y",
                    tag=y_var_tag,
                    callback=update_plot_inputs,
                    user_data=plot_data,
                )
                dpg.add_input_float(label="X Start", tag=x_start_tag, default_value=0.0)
                dpg.add_input_float(label="X End", tag=x_end_tag, default_value=10.0)
                dpg.add_input_float(label="Step", tag=x_step_tag, default_value=1.0)
                dpg.add_separator()
                with dpg.group(tag=const_group_tag):
                    pass
                dpg.add_button(
                    label="Plot", callback=plot_callback, user_data=plot_data
                )
                dpg.add_same_line()
                dpg.add_button(
                    label="Export CSV",
                    callback=lambda s, a, u: dpg.show_item(f"{window_tag}_csv_dialog"),
                )
                with dpg.file_dialog(
                    directory_selector=False,
                    show=False,
                    callback=export_csv_callback,
                    tag=f"{window_tag}_csv_dialog",
                    user_data=plot_data,
                ):
                    dpg.add_file_extension(".csv", color=(0, 255, 0, 255))
                with dpg.plot(label="Plot", height=200, tag=plot_tag):
                    dpg.add_plot_axis(dpg.mvXAxis, label="X")
                    with dpg.plot_axis(dpg.mvYAxis, label="Y", tag=axis_y_tag):
                        dpg.add_line_series([], [], tag=plot_series_tag)

            with dpg.tab(label="Defaults"):
                def_tags: Dict[str, str] = {}
                for var in eq.vars:
                    tag = f"{window_tag}_def_{var}"
                    dpg.add_input_text(
                        label=var, tag=tag, default_value=default_values.get(var, "")
                    )
                    def_tags[var] = tag
                dpg.add_button(
                    label="Save", callback=export_defaults_default, user_data=def_tags
                )
                dpg.add_same_line()
                dpg.add_button(
                    label="Save As",
                    callback=lambda s, a, u: dpg.show_item(f"{window_tag}_def_export"),
                )
                dpg.add_same_line()
                dpg.add_button(
                    label="Load", callback=import_defaults_default, user_data=def_tags
                )
                with dpg.file_dialog(
                    directory_selector=False,
                    show=False,
                    callback=export_defaults_callback,
                    tag=f"{window_tag}_def_export",
                    user_data=def_tags,
                ):
                    dpg.add_file_extension(".yaml", color=(0, 255, 0, 255))
                with dpg.file_dialog(
                    directory_selector=False,
                    show=False,
                    callback=import_defaults_callback,
                    tag=f"{window_tag}_def_import",
                    user_data=def_tags,
                ):
                    dpg.add_file_extension(".yaml", color=(0, 255, 0, 255))

        # initial population of constant inputs
        update_plot_inputs(None, None, plot_data)


# Build context menu overview
@log_calls
def build_context_menu(width=320, height=390):
    """Open the main window showing all available formulas."""
    logger.info("Launching Lambda Explorer GUI")
    dpg.create_context()
    dpg.configure_app(docking=True, docking_space=True)
    setup_logger_window()
    _next_pos[0], _next_pos[1] = 20, 20
    with dpg.window(
        label="Formula Overview",
        tag="main_window",
        width=300,
        height=350,
        pos=_get_next_pos(),
    ):
        dpg.add_text("Click formulas to open")
        topics = formula_registry.formulas_by_topic()
        for topic in sorted(topics):
            dpg.add_separator()
            dpg.add_text(topic, color=[255, 255, 0])
            for name in topics[topic]:
                item_tag = f"item_{name}"
                dpg.add_text(name, tag=item_tag)

                # create an item handler registry to manage click events
                with dpg.item_handler_registry() as handler:
                    dpg.add_item_clicked_handler(
                        callback=open_formula_window, user_data=name
                    )
                dpg.bind_item_handler_registry(item_tag, handler)
        dpg.add_separator()
        dpg.add_button(label="View logs", callback=show_log_window)
        dpg.add_same_line()
        dpg.add_button(label="Settings", callback=show_settings_window)
        dpg.add_same_line()
        dpg.add_button(label="Formula Editor", callback=show_formula_editor)

    # restore previously open formula windows before layout loading
    for name in load_open_windows():
        if name in formula_classes:
            open_formula_window(None, None, name)
    dpg.create_viewport(title="Formula Overview", width=width, height=height)
    if ICON_PATH.exists():
        try:
            dpg.set_viewport_small_icon(str(ICON_PATH))
            dpg.set_viewport_large_icon(str(ICON_PATH))
        except Exception as exc:  # pragma: no cover - GUI
            logger.warning("Failed to set viewport icon: %s", exc)
    else:
        logger.debug("Icon file not found: %s", ICON_PATH)
    dpg.setup_dearpygui()
    load_layout()
    dpg.show_viewport()
    dpg.show_item("main_window")
    dpg.maximize_viewport()

    # dock windows on startup
    vp_w = dpg.get_viewport_client_width()
    vp_h = dpg.get_viewport_client_height()

    # main window (context menu) on the left
    # dpg.set_primary_window("main_window", True)
    dpg.set_item_pos("main_window", [10, 10])
    dpg.set_item_height("main_window", vp_h - 220)

    # log window at the bottom
    dpg.show_item(log_window_tag)
    lh = dpg.get_item_height(log_window_tag)
    dpg.set_item_width(log_window_tag, vp_w - 20)
    dpg.set_item_pos(log_window_tag, [10, vp_h - lh - 10])

    def _on_exit():
        open_windows = [
            name
            for name in formula_classes
            if dpg.does_item_exist(f"win_{name}") and dpg.is_item_shown(f"win_{name}")
        ]
        save_open_windows(open_windows)
        save_layout()

    dpg.set_exit_callback(_on_exit)
    dpg.start_dearpygui()
    dpg.destroy_context()
    logger.info("GUI closed")


if __name__ == "__main__":
    build_context_menu()

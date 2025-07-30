"""
This module contains the components for the filters menu in the plot.

# NOTE:
1. All toggles for (de-)activating filters should have a type of "apply-<filter_name>", where <filter_name> does not contain any spaces or '-'.
2. All filter options should have a type of "<filter_name>-<slider_name>", where <filter_name> & <slider_name> do not contain any spaces or '-'.

"""

from dash import dcc, html
import dash_daq as daq

# Local imports
from qimchi.components.figures import QimchiFigure
from qimchi.state import (
    load_state_from_disk,
    DEFAULT_SAVGOL_OPTS,
    DEFAULT_SMA_WINDOW,
    DEFAULT_NORM_AXIS,
    DEFAULT_GC_OPTS,
    DEFAULT_LC_OPTS,
    DEFAULT_SC_OPTS,
    DEFAULT_POLYFIT_OPTS,
    DEFAULT_RI_OPTS,  # noqa # TODOLATER: Unused
    DEFAULT_ROTA_OPTS,
)


# TODOLATER: These helper components can be used in plots.py.
def _horiz_rule() -> html.Hr:
    """
    Styled horizontal rule component with styling.

    """
    return html.Hr(
        style={
            "margin": "0.5rem 0 1rem",
            "border": "0.1px dashed gray",
            "opacity": "0.25",
        }
    )


def _label_slider(
    fig_id: str,
    label: str,
    type_str: str,
    slider_props: dict,
    slider_type: str = "Slider",
) -> html.Div:
    """
    Styled Label-(Range-)Slider component.

    Args:
        fig_id (str): Unique identifier for the figure in the plot.
        label (str): Label for the slider.
        type_str (str): Type of the slider.
        slider_type (str): Type of the slider. One of "Slider" or "RangeSlider".
        **slider_props (dict): Slider properties. The keys are:
            - min (int): Minimum value.
            - max (int): Maximum value.
            - step (int | float): Step value.
            - val (int): Initial value.
            - marks (dict): Marks for the slider. Optional.

    Returns:
        dash.html.Div: Slider or RangeSlider component with Label and styling.

    """
    _min, _max, _step, _val, _marks = (
        slider_props.get("min"),
        slider_props.get("max"),
        slider_props.get("step"),
        slider_props.get("val"),
        slider_props.get("marks"),
    )

    slider = (
        dcc.RangeSlider(
            id={"index": fig_id, "type": type_str, "menu": "filter-opts"},
            min=_min,
            max=_max,
            step=_step,
            value=_val,
            updatemode="drag",
            persistence=True,
            persistence_type="local",
            className="column is-10 mx-0 my-2 px-0",
        )
        if slider_type == "RangeSlider"
        else dcc.Slider(
            id={"index": fig_id, "type": type_str, "menu": "filter-opts"},
            min=_min,
            max=_max,
            step=_step,
            value=_val,
            updatemode="drag",
            tooltip={
                "placement": "bottom",
                "always_visible": True,
            },
            persistence=True,
            persistence_type="local",
            className="column is-10 mx-0 my-2 px-0",
        )
    )

    if _marks:
        slider.marks = _marks

    return html.Div(
        [
            html.Label(
                label,
                className="column is-2 px-0",
                style={"fontWeight": "bold"},
            ),
            slider,
        ],
        className="column is-full is-flex p-0",
    )


def _label_toggle(
    fig_id: str,
    label: str,
    type_str: str,
    val: bool,
    div_title: str,
) -> html.Div:
    """
    Styled Label-ToggleSwitch component.

    Args:
        fig_id (str): Unique identifier for the figure in the plot.
        label (str): Label for the toggle switch.
        type_str (str): Type of the toggle switch.
        value (bool): Initial value.
        div_title (str): Title for the div.

    Returns:
        dash.html.Div: ToggleSwitch component with Label and styling.

    """
    return html.Div(
        [
            html.Label(
                label,
                className="column is-10 px-0",
                style={"fontWeight": "bold"},
            ),
            daq.ToggleSwitch(
                id={"index": fig_id, "type": type_str, "menu": "filter-apply"},
                value=val,
                persistence=True,
                persistence_type="local",
                className="column is-2 px-0",
            ),
        ],
        className="column is-full is-flex px-2 py-0 mt-2 has-background-grey-lighter",
        title=div_title,
    )


def _label_dropdown(
    fig_id: str,
    label: str,
    type_str: str,
    options: list,
    val: str,
    placeholder: str,
    div_title: str,
) -> html.Div:
    """
    Styled Label-Dropdown component.

    Args:
        fig_id (str): Unique identifier for the figure in the plot.
        label (str): Label for the dropdown.
        type_str (str): Type of the dropdown.
        options (list): List of options for the dropdown.
        value (str): Initial value.
        placeholder (str): Placeholder for the dropdown.
        div_title (str): Title for the div.

    Returns:
        dash.html.Div: Dropdown component with Label and styling.

    """
    return html.Div(
        [
            html.Label(
                label,
                className="column is-2 px-0",
                style={"fontWeight": "bold"},
            ),
            dcc.Dropdown(
                id={"index": fig_id, "type": type_str, "menu": "filter-opts"},
                options=options,
                value=val,
                placeholder=placeholder,
                persistence=True,
                persistence_type="local",
                # NOTE: className="column is-10" refuses to work here
                style={"width": "100%", "margin": "0", "padding": "0"},
            ),
        ],
        className="column is-full is-flex p-0",
        title=div_title,
    )


def _log_scale_comp(fig_id: str, applied_filters_order: list) -> dcc.Tab:
    """
    Log-scaling component. For both 1D LinePlots and 2D HeatMaps.

    Args:
        fig_id (str): Unique identifier for the figure in the plot.
        applied_filters_order (list): List of applied filters.

    Returns:
        dcc.Tab: Log-scaling component.

    """
    log_scale_toggled = "log_scale" in applied_filters_order
    log_scaling = dcc.Tab(
        label="Log Scale",
        children=[
            _label_toggle(
                fig_id,
                "Apply Log-scaling",
                "apply-log_scale",
                log_scale_toggled,
                div_title="Apply log-scaling to the plot",
            )
        ],
        className="column p-1",
    )

    return log_scaling


def _flip_comp(fig_id: str, applied_filters_order: list) -> dcc.Tab:
    """
    Flip component. Only for 2D HeatMaps.

    Args:
        fig_id (str): Unique identifier for the figure in the plot.
        applied_filters_order (list): List of applied filters.

    Returns:
        dcc.Tab: Flip component.

    """
    flip_toggled = "flip" in applied_filters_order
    flip = dcc.Tab(
        label="Flip",
        className="p-1",
        children=[
            _label_toggle(
                fig_id,
                "Flip HeatMap",
                "apply-flip",
                flip_toggled,
                div_title="Flip the plot",
            )
        ],
    )

    return flip


def _fit_comp(fig_id: str, applied_filters_order: list) -> dcc.Tab:
    """
    PolyFit component. Only for 1D LinePlots.

    Args:
        fig_id (str): Unique identifier for the figure in the plot.
        applied_filters_order (list): List of applied filters.

    Returns:
        dcc.Tab: PolyFit component.

    """
    fit_toggled = "polyfit" in applied_filters_order
    fit = dcc.Tab(
        label="PolyFit",
        className="p-1",
        children=[
            _label_toggle(
                fig_id,
                "Apply PolyFit",
                "apply-polyfit",
                fit_toggled,
                div_title="Apply polynomial fitting to the plot",
            ),
            _horiz_rule(),
            _label_slider(
                fig_id,
                "Degree",
                "polyfit-deg",
                slider_type="Slider",
                slider_props={
                    "min": 1,
                    "max": 5,
                    "step": 1,
                    "val": DEFAULT_POLYFIT_OPTS["deg"],
                },
            ),
            _label_slider(
                fig_id,
                "Window",
                "polyfit-window",
                slider_type="RangeSlider",
                slider_props={
                    "min": DEFAULT_POLYFIT_OPTS["window"][0],
                    "max": DEFAULT_POLYFIT_OPTS["window"][1],
                    "step": 0.01,
                    "val": DEFAULT_POLYFIT_OPTS["window"],
                    "marks": {0: "0", 1: "1"},
                },
            ),
        ],
    )

    return fit


def _smooth_comp(fig_id: str, applied_filters_order: list, num_axes: int) -> dcc.Tab:
    """
    Smoothing-related components, based on the number of axes in the figure. Has:
    - Savitzky-Golay (1D LinePlots & 2D HeatMaps)
    - Simple Moving Average (1D LinePlots)

    Args:
        fig_id (str): Unique identifier for the figure in the plot.
        applied_filters_order (list): List of applied filters.
        num_axes (int): Number of axes in the figure.

    Returns:
        dcc.Tab: Smoothing-related components.

    """
    _is_hmap = num_axes == 2

    # Savitzky-Golay
    savgol_toggled = "savgol" in applied_filters_order
    sav_gol = dcc.Tab(
        label="SavGol",
        className="p-1",
        children=[
            _label_toggle(
                fig_id,
                "Apply SavGol",
                "apply-savgol",
                savgol_toggled,
                div_title="Apply Savitzky-Golay smoothing to the plot",
            ),
            _horiz_rule(),
            # savgol_filter options
            _label_slider(
                fig_id,
                "Window",
                "savgol-window",
                slider_type="Slider",
                slider_props={
                    "min": 2,
                    "max": 20,
                    "step": 1,
                    "val": DEFAULT_SAVGOL_OPTS["window"],
                },
            ),
            _label_slider(
                fig_id,
                "Polyorder",
                "savgol-polyorder",
                slider_type="Slider",
                slider_props={
                    "min": 2,
                    "max": DEFAULT_SAVGOL_OPTS["window"] - 1,
                    "step": 1,
                    "val": DEFAULT_SAVGOL_OPTS["polyorder"],
                },
            ),
            # Axis to smooth over | axis: int
            _label_dropdown(
                fig_id,
                "Along Axis",
                "savgol-axis",
                [
                    {"label": "X", "value": 0},
                    {"label": "Y", "value": 1},
                    {
                        "label": "Z",
                        # NOTE: savgol_filter supports only 1D. We emulate 2D by applying it to each axis separately.
                        "value": 2,
                    },
                ],
                DEFAULT_SAVGOL_OPTS["axis"],
                "Select axis along which to smooth",
                div_title="Select axis along which to smooth",
            )
            if _is_hmap
            else None,
            # deriv: int
            _label_slider(
                fig_id,
                "Derivative",
                "savgol-deriv",
                slider_type="Slider",
                slider_props={
                    "min": 0,
                    "max": 5,
                    "step": 1,
                    "val": DEFAULT_SAVGOL_OPTS["deriv"],
                },
            ),
            # Sample spacing | delta: float
            # NOTE: Only used if deriv > 0.
            _label_slider(
                fig_id,
                "Delta",
                "savgol-delta",
                slider_type="Slider",
                slider_props={
                    "min": 1.0,
                    "max": 10.0,
                    "val": DEFAULT_SAVGOL_OPTS["delta"],
                },
            ),
            # Type of padding | mode: str
            _label_dropdown(
                fig_id,
                "Mode",
                "savgol-mode",
                [
                    {"label": "interp", "value": "interp"},
                    {"label": "nearest", "value": "nearest"},
                    {"label": "wrap", "value": "wrap"},
                    {"label": "mirror", "value": "mirror"},
                    {"label": "constant", "value": "constant"},
                ],
                DEFAULT_SAVGOL_OPTS["mode"],
                "Select mode",
                div_title="Select mode for the Savitzky-Golay filter",
            ),
            # Fill value if mode is 'constant' | cval: float
            _label_slider(
                fig_id,
                "Constant Fill",
                "savgol-cval",
                slider_type="Slider",
                slider_props={
                    "min": 0.0,
                    "max": 1,
                    "val": DEFAULT_SAVGOL_OPTS["cval"],
                },
            ),
        ],
    )

    # Simple Moving Average
    sma_toggled = "sma" in applied_filters_order
    sma = dcc.Tab(
        label="SMA",
        className="p-1",
        children=[
            _label_toggle(
                fig_id,
                "Apply SMA",
                "apply-sma",
                sma_toggled,
                div_title="Calculate Simple Moving Average for the plot",
            ),
            html.Div(
                html.P(
                    [
                        html.Strong("⚠️ WARNING: ", style={"color": "#050505"}),
                        "Output length is same as the input length because of ",
                        html.Code("mode='same'"),
                        " in ",
                        html.Code("np.convolve()"),
                        ". Beware of the edge effects.",
                    ],
                    style={
                        "fontSize": "0.85rem",
                        "margin": "0",
                    },
                ),
                style={
                    "padding": "0.5rem 1rem",
                    "margin": "0.5rem 0",
                    "backgroundColor": "#fff8c5",
                    "border": "1px solid #f0b429",
                    "borderRadius": "4px",
                    "borderLeft": "4px solid #f0b429",
                },
            ),
            _horiz_rule(),
            _label_slider(
                fig_id,
                "Window",
                "sma-window",
                slider_type="Slider",
                slider_props={
                    "min": 2,
                    "max": 20,
                    "step": 1,
                    "val": DEFAULT_SMA_WINDOW,
                },
            ),
        ],
    )

    smooth_options = [sav_gol]
    if num_axes == 1:
        smooth_options.append(sma)

    smooth_options = dcc.Tabs(
        smooth_options,
        id={"type": "smooth-options-tabs", "index": fig_id},
        persistence=True,
        persistence_type="local",
    )

    smooth = dcc.Tab(label="Smooth", className="p-1", children=smooth_options)

    return smooth


def _max_norm_comp(
    sess_id: str,
    fig_id: str,
    applied_filters_order: list,
) -> dcc.Tab:
    """
    Max-Normalize component. For both 1D LinePlots and 2D HeatMaps.

    Args:
        sess_id (str): Session ID to load the state for
        fig_id (str): Unique identifier for the figure in the plot
        applied_filters_order (list): List of applied filters

    Returns:
        dcc.Tab: Max-Normalize component.

    """
    _state = load_state_from_disk(sess_id)

    is_hmap = _state.plot_states[fig_id]["plot_type"] == "HeatMap"
    max_norm_toggled = "normalize" in applied_filters_order
    max_norm = dcc.Tab(
        label="Normalize",
        className="p-1",
        children=[
            _label_toggle(
                fig_id,
                "Apply Normalize",
                "apply-normalize",
                max_norm_toggled,
                div_title="Max-normalize the plot",
            ),
            _horiz_rule() if is_hmap else None,
            (
                _label_dropdown(
                    fig_id,
                    "Along Axis",
                    "normalize-axis",
                    [
                        {"label": "X", "value": "x"},
                        {"label": "Y", "value": "y"},
                        {"label": "Z", "value": "z"},
                    ],
                    DEFAULT_NORM_AXIS,
                    "Select axis label",
                    div_title="Select axis label to normalize along",
                )
                if is_hmap
                else None
            ),
        ],
    )

    return max_norm


def _diff_comp(fig_id: str, applied_filters_order: list, num_axes: int) -> dcc.Tab:
    """
    Differentiate component, based on the number of axes in the figure. Has:
    - Differentiate (1D LinePlots)
    - Differentiate X & Y (2D HeatMaps)

    Args:
        fig_id (str): Unique identifier for the figure in the plot.
        applied_filters_order (list): List of applied filters.
        num_axes (int): Number of axes in the figure.

    Returns:
        dcc.Tab: Differentiate component.

    """
    diff_opts = []
    if num_axes == 1:
        diff_toggled = "diff" in applied_filters_order
        diff_opts = [
            _label_toggle(
                fig_id,
                "Differentiate",
                "apply-diff",
                diff_toggled,
                div_title="Take first derivative",
            ),
        ]
    elif num_axes == 2:
        diff_x_toggled = "diff_x" in applied_filters_order
        differentiate_x = _label_toggle(
            fig_id,
            "Differentiate along Y",
            "apply-diff_x",
            diff_x_toggled,
            div_title="Take first derivative along the Y-axis",
        )

        diff_y_toggled = "diff_y" in applied_filters_order
        differentiate_y = _label_toggle(
            fig_id,
            "Differentiate along X",
            "apply-diff_y",
            diff_y_toggled,
            div_title="Take first derivative along the X-axis",
        )

        diff_opts = [
            differentiate_x,
            differentiate_y,
        ]

    diff = dcc.Tab(
        label="Differentiate",
        className="p-1",
        children=diff_opts,
    )
    return diff


def _contrast_comp(fig_id: str, applied_filters_order: list) -> dcc.Tab:
    """
    Contrast-related components. Only for 2D HeatMaps. Has:
    - Gamma Correction
    - Log Correction
    - Sigmoid Correction
    - Rescale Intensity

    Args:
        fig_id (str): Unique identifier for the figure in the plot.
        applied_filters_order (list): List of applied filters.

    Returns:
        dcc.Tab: Contrast-related components.

    """
    gamma_corr_toggled = "gamma_corr" in applied_filters_order
    log_corr_toggled = "log_corr" in applied_filters_order
    sig_corr_toggled = "sig_corr" in applied_filters_order
    rescale_intensity_toggled = "rescale_intensity" in applied_filters_order

    gamma = dcc.Tab(
        label="Gamma Correction",
        children=[
            _label_toggle(
                fig_id,
                "Apply Gamma Correction",
                "apply-gamma_corr",
                gamma_corr_toggled,
                div_title="Apply gamma correction to the plot",
            ),
            _horiz_rule(),
            _label_slider(
                fig_id,
                "Gamma (γ)",
                "gamma_corr-gamma",
                slider_type="Slider",
                slider_props={
                    "min": 0,
                    "max": 10,
                    "step": 0.1,
                    "val": DEFAULT_GC_OPTS["gamma"],
                    "marks": {0: "0", 10: "10"},
                },
            ),
            _label_slider(
                fig_id,
                "Gain",
                "gamma_corr-gain",
                slider_type="Slider",
                slider_props={
                    "min": 1,
                    "max": 10,
                    "step": 0.1,
                    "val": DEFAULT_GC_OPTS["gain"],
                    "marks": {1: "1", 10: "10"},
                },
            ),
        ],
        className="column p-1",
    )

    log_corr = dcc.Tab(
        label="Log Correction",
        children=[
            _label_toggle(
                fig_id,
                "Apply Log Correction",
                "apply-log_corr",
                log_corr_toggled,
                div_title="Apply log correction to the plot",
            ),
            _horiz_rule(),
            html.Div(
                [
                    html.Label(
                        "Gain",
                        className="column is-1 px-0",
                        style={"fontWeight": "bold"},
                    ),
                    dcc.Slider(
                        id={
                            "index": fig_id,
                            "type": "log_corr-gain",
                            "menu": "filter-opts",
                        },
                        min=1,
                        max=10,
                        step=0.1,
                        marks={1: "1", 10: "10"},
                        value=DEFAULT_LC_OPTS["gain"],
                        updatemode="drag",
                        tooltip={
                            "placement": "bottom",
                            "always_visible": True,
                        },
                        persistence=True,
                        persistence_type="local",
                        className="column is-9 mx-0 my-2 px-0",
                    ),
                    daq.ToggleSwitch(
                        label="Invert Log",
                        labelPosition="bottom",
                        id={
                            "index": fig_id,
                            "type": "log_corr-inv",
                            "menu": "filter-opts",
                        },
                        value=DEFAULT_LC_OPTS["inv"],
                        persistence=True,
                        persistence_type="local",
                        className="column is-2 m-0 px-0",
                    ),
                ],
                className="column is-full is-flex p-0",
            ),
        ],
        className="column p-1",
    )

    sig_corr = dcc.Tab(
        label="Sigmoid Correction",
        children=[
            _label_toggle(
                fig_id,
                "Apply Sigmoid Correction",
                "apply-sig_corr",
                sig_corr_toggled,
                div_title="Apply sigmoid correction to the plot",
            ),
            _horiz_rule(),
            _label_slider(
                fig_id,
                "Cutoff",
                "sig_corr-cutoff",
                slider_type="Slider",
                slider_props={
                    "min": 0,
                    "max": 1,
                    "step": 0.1,
                    "val": DEFAULT_SC_OPTS["cutoff"],
                    "marks": {0: "0", 1: "1"},
                },
            ),
            _label_slider(
                fig_id,
                "Gain",
                "sig_corr-gain",
                slider_type="Slider",
                slider_props={
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "val": DEFAULT_SC_OPTS["gain"],
                    "marks": {1: "1", 100: "100"},
                },
            ),
        ],
        className="column p-1",
    )

    rescale_intensity = dcc.Tab(
        label="Rescale Intensity",
        children=[
            _label_toggle(
                fig_id,
                "Rescale Intensity",
                "apply-rescale_intensity",
                rescale_intensity_toggled,
                div_title="Rescale intensity of the plot",
            )
            # TODOLATER: Can allow specifying the range to scale to.
            # TODOLATER: See: https://scikit-image.org/docs/stable/api/skimage.exposure.html#skimage.exposure.rescale_intensity
        ],
        className="column p-1",
    )

    contrast_options = dcc.Tabs(
        [
            gamma,
            log_corr,
            sig_corr,
            rescale_intensity,
        ],
        id={"type": "contrast-options-tabs", "index": fig_id},
        persistence=True,
        persistence_type="local",
    )

    contrast = dcc.Tab(
        label="Contrast",
        className="p-1",
        children=contrast_options,
    )

    return contrast


def _rota_comp(fig_id: str, applied_filters_order: list) -> dcc.Tab:
    """
    Rotate component. Only for 2D HeatMaps.

    Args:
        fig_id (str): Unique identifier for the figure in the plot.
        applied_filters_order (list): List of applied filters.

    Returns:
        dcc.Tab: Rotate component.

    """
    rotate_toggled = "rotate" in applied_filters_order
    rotate = dcc.Tab(
        label="Rotate",
        className="p-1",
        children=[
            _label_toggle(
                fig_id,
                "Rotate HeatMap",
                "apply-rotate",
                rotate_toggled,
                div_title="Rotate the plot",
            ),
            # _horiz_rule(), # TODO: Looks out of place. Your call @s.anupam.
            daq.Knob(
                id={"type": "rotate-angle", "index": fig_id, "menu": "filter-opts"},
                label={
                    "label": "Angle",
                    "style": {"fontSize": "1.2em", "fontWeight": "bold"},
                },
                labelPosition="bottom",
                value=DEFAULT_ROTA_OPTS["angle"],
                min=-180,
                max=180,
                size=200,
                scale={
                    "start": -180,
                    "labelInterval": 45,
                    "custom": {
                        -180: "-180",
                        -135: "-135",
                        -90: "-90",
                        -45: "-45",
                        0: "0",
                        45: "45",
                        90: "90",
                        135: "135",
                        180: "180",
                    },
                },
                persistence=True,
                persistence_type="local",
            ),
        ],
    )

    return rotate


def content_filters(
    sess_id: str,
    fig: QimchiFigure,
    fig_id: str,
) -> html.Div:
    """
    Generates the filters menu for the plot.

    Args:
        sess_id (str): Session ID to identify the data.
        fig (QimchiFigure): QimchiFigure object.
        fig_id (str): Unique identifier for the figure in the plot.

    Returns:
        dash.html.Div: Filters menu container.

    """
    _state = load_state_from_disk(sess_id)

    fig_plot_menu = _state.plot_states[fig_id]["plots_menu"]
    applied_filters_order: list = _state.plot_states[fig_id]["filters_order"]
    num_axes = fig.num_axes

    # "Common" filters
    filters = [
        _log_scale_comp(fig_id, applied_filters_order),
        # NOTE: Depending on the number of axes, these filters will be different
        _smooth_comp(fig_id, applied_filters_order, num_axes),
        _diff_comp(fig_id, applied_filters_order, num_axes),
        _max_norm_comp(sess_id, fig_id, applied_filters_order),
    ]
    # 1D LinePlot filters
    if num_axes == 1:
        filters.extend(
            [
                _fit_comp(fig_id, applied_filters_order),
            ]
        )
    # 2D HeatMap filters
    elif num_axes == 2:
        filters.extend(
            [
                _contrast_comp(fig_id, applied_filters_order),
                _rota_comp(fig_id, applied_filters_order),
                _flip_comp(fig_id, applied_filters_order),
            ]
        )

    return html.Div(
        [
            dcc.Tabs(
                filters,
                id={"type": "content-filters-tabs", "index": fig_id},
                persistence=True,
                persistence_type="local",
                className="column is-full px-0 py-2",
            )
        ],
        style={"display": fig_plot_menu["content_filters_disp"]},
        id={"type": "content-filters", "index": fig_id},
    )

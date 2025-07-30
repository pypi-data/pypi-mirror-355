from pathlib import Path
from datetime import datetime
from string import Template

from dash import Input, Output, State, callback, html, dcc
from dash.exceptions import PreventUpdate

# Local imports
from qimchi.state import load_state_from_disk
from qimchi.logger import logger


# Default Frontmatter - Obsidian style
FRONTMATTER = Template(
    """---
Last Saved: ${timestamp}
Filename: ${filename}

---"""
)
DEFAULT_NOTES = "Type your notes here..."


def _get_notes(sess_id: str) -> str:
    """
    Utility function to load or create notes

    Args:
        sess_id (str): Session ID to load the state for

    Returns:
        str: Notes to be displayed in the notes viewer

    """
    _state = load_state_from_disk(sess_id)

    base = Path(_state.measurement_path)
    if not _state.measurement_last_fmt:
        logger.debug("Notes | No measurement found")
        return DEFAULT_NOTES

    path = base.parent / base.stem / (base.stem + ".md")

    if path.exists():
        logger.debug(f"Notes | Loading from: {path}")
        with open(path, "r") as f:
            notes = f.read()

        # Remove frontmatter
        notes = notes.split("---\n")
        notes = "---\n".join(notes[2:])

        return notes

    else:
        logger.debug(f"Notes | Creating new at: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)

        notes_to_write = (
            FRONTMATTER.substitute(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                filename=path.stem,
            )
            + "\n"
            + DEFAULT_NOTES
        )

        # Save to file
        logger.debug(f"Notes | NEW | Saving to: {path}")
        with open(path, "w") as f:
            f.write(notes_to_write)

        return DEFAULT_NOTES


def notes_viewer() -> html.Div:
    """
    Notes viewer

    Returns:
        dash.html.Div: Div element containing a textarea for notes and a collapsible markdown viewer

    """
    return html.Div(
        [
            html.Div(
                [
                    html.H5(html.B("Notes"), className="is-size-5 is-4 is-pulled-left"),
                    # Toggle button to show/hide notes
                    html.Button(
                        html.I(className="fa-solid fa-eye-slash"),
                        id="hide-notes",
                        className="button is-info is-pulled-right",
                    ),
                ],
                className="column is-full mt-0",
                style={
                    "minHeight": "4rem",
                },
            ),
            html.Div(
                [
                    html.Button(
                        html.I(className="fa-solid fa-eye-slash"),
                        id="hide-preview",
                        className="button is-info is-pulled-left mx-2 my-0",
                        style={
                            "maxHeight": "280px",
                        },
                    ),
                    dcc.Textarea(
                        id="notes-area",
                        # placeholder="Type your notes here...",
                        value=DEFAULT_NOTES,
                        className="column ml-0 mr-2 p-3",
                        style={
                            "minHeight": "175px",
                            "maxHeight": "278px",
                        },
                    ),
                    html.Div(
                        dcc.Markdown(
                            id="notes-preview",
                            className="content m-0 p-0",
                            mathjax=True,
                            # NOTE: Local
                            dangerously_allow_html=True,
                            style={
                                "minHeight": "175px",
                                "maxHeight": "270px",
                                "overflowY": "scroll",
                            },
                        ),
                        id="notes-preview-div",
                        className="column m-2 p-3",
                        style={
                            "minHeight": "175px",
                            "maxHeight": "278px",
                            "overflowY": "scroll",
                        },
                    ),
                ],
                className="columns is-multiline box m-0 p-1",
                style={"maxHeight": "300px"},
                id="notes-viewer",
            ),
        ],
    )


@callback(
    Output("notes-preview-div", "style"),
    Output("hide-preview", "children"),
    Input("hide-preview", "n_clicks"),
)
def show_hide_preview(n_clicks: int) -> tuple:
    """
    Callback to show or hide the markdown preview

    Args:
        n_clicks (int): Number of times the button has been clicked

    Returns:
        tuple: Style to display the markdown preview and the button icon

    """
    if n_clicks is None or n_clicks % 2 == 0:
        return {"display": "block"}, html.I(className="fa-solid fa-eye-slash")
    else:
        return {"display": "none"}, html.I(className="fa-solid fa-eye")


@callback(
    Output("notes-preview", "children"),
    State("session-id", "data"),
    Input("notes-area", "value"),
)
def update_output(sess_id: str, new_notes: str) -> str:
    """
    Callback to update the markdown preview

    Args:
        sess_id (str): Session ID to load the state for
        new_notes (str): Value of the notes textarea

    Returns:
        str: Markdown preview to be displayed

    """
    _state = load_state_from_disk(sess_id)

    if new_notes is None:
        logger.debug("Notes | UPDATE | No notes to update")
        raise PreventUpdate
    # Save to file and update Last Saved
    base = Path(_state.measurement_path)
    if not _state.measurement_last_fmt:
        logger.debug("Notes | UPDATE | No measurement found")
        raise PreventUpdate

    path = base.parent / base.stem / (base.stem + ".md")

    if path.exists():
        logger.debug(f"Notes | UPDATE | Updating notes for: {path}")
        logger.debug(f"Notes | UPDATE | Updating notes with: {new_notes}")
        notes = (
            FRONTMATTER.substitute(
                timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                filename=path.stem,
            )
            + "\n"
            + new_notes
        )

        # Save to file
        logger.debug(f"Notes | UPDATE | Saving to: {path}")
        with open(path, "w") as f:
            f.write(notes)

        # Update preview
        return rf"{new_notes}"

    else:
        logger.debug(f"Notes | UPDATE | No notes found at: {path}")
        return DEFAULT_NOTES


@callback(
    # TODOLATER: Figure out how to push plots to the notes
    Output("notes-area", "value"),  # , allow_duplicate=True),
    State("session-id", "data"),
    Input("load-signal", "data"),
    # TODOLATER:
    # BUG: True required for `allow_duplicate`, but it makes the notes non-persistent.
    # BUG: But it is needed to allow multiple callbacks with `notes-area` as output. So, ¯\_(ツ)_/¯
    # prevent_initial_call=True,
)
def update_notes(sess_id: str, sig: int) -> str:
    """
    Callback to update notes & preview

    Args:
        sess_id (str): Session ID to load the state for
        sig (int): Signal to indicate that data has been updated

    Returns:
        str: Notes to be displayed

    """
    notes = _get_notes(sess_id)
    if sig in [None, 0]:
        return notes

    logger.debug("Notes | Updating notes as load-signal has changed.")
    return notes


@callback(
    Output("notes-viewer", "className", allow_duplicate=True),
    Output("hide-notes", "children"),
    Input("hide-notes", "n_clicks"),
    prevent_initial_call=True,
)
def show_hide_notes(n_clicks: int) -> tuple:
    """
    Callback to show or hide the notes viewer

    Args:
        n_clicks (int): Number of times the button has been clicked

    Returns:
        tuple: className to display the notes viewer and the updated button icon

    """
    if n_clicks is None or n_clicks % 2 == 0:
        return "columns is-multiline box m-0 p-1", html.I(
            className="fa-solid fa-eye-slash"
        )
    else:
        return "columns is-multiline box m-0 p-1 is-hidden", html.I(
            className="fa-solid fa-eye"
        )


# TODOLATER: Figure out how to push plots to the notes. See update_notes() above.
# @callback(
#     Output({"index": ALL, "type": "notes-store"}, "data", allow_duplicate=True),
#     Output("notes-area", "value", allow_duplicate=True),
#     Input({"index": ALL, "type": "notes-store"}, "data"),
#     prevent_initial_call=True,
# )
# def update_notes_from_store(notes_from_stores: list) -> Tuple[list, str]:
#     """
#     Callback to update notes from stores and to empty the stores after

#     Args:
#         notes_from_stores (list): List of notes from stores

#     Returns:
#         Tuple[list, str]: List of empty notes stores and the notes to be displayed

#     """
#     logger.debug(f"notes_from_stores : {notes_from_stores}")

#     # If notes found in stores, return the first one and empty all stores
#     empty_notes_stores = [None] * len(notes_from_stores)
#     for notes in notes_from_stores:
#         if notes:
#             logger.debug(f"Notes | Updating notes from store: {notes}")
#             return empty_notes_stores, notes

#     # If no notes found in stores, prevent update
#     logger.debug("Notes | No notes found in stores")
#     return empty_notes_stores, _get_notes()

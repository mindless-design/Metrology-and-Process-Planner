"""Best-effort Qt region rendering for the KLayout session editor."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from metrology_process_planner.infrastructure.klayout.session_editor_region_widgets import (
    add_widget,
    attach_region,
    button,
    label,
    qt_state,
    region_container,
)
from metrology_process_planner.infrastructure.klayout.session_editor_region_widgets import (
    layout as make_layout,
)
from metrology_process_planner.workflows.editor.view_models import (
    EditorAction,
    EditorActionType,
    MetadataField,
)

ActionCallback = Callable[[EditorAction], None]


def render_text_region(pya: Any, window: Any, key: str, rows: tuple[object, ...]) -> None:
    """Render a text-oriented editor region when Qt classes are available."""

    labels = tuple(_row_text(row) for row in rows)
    qt_state(window).setdefault("qt_region_labels", {})[key] = labels
    container = region_container(pya)
    if container is None:
        return
    layout = make_layout(pya, container)
    for text in labels:
        add_widget(layout, label(pya, text))
    attach_region(window, key, container)


def render_action_region(
    pya: Any,
    window: Any,
    key: str,
    actions: tuple[EditorAction, ...],
) -> None:
    """Render an action-oriented editor region when Qt classes are available."""

    labels = tuple(action.label for action in actions)
    qt_state(window).setdefault("qt_region_labels", {})[key] = labels
    container = region_container(pya)
    if container is None:
        return
    layout = make_layout(pya, container)
    for action in actions:
        add_widget(layout, button(pya, action.label))
    attach_region(window, key, container)


def render_metadata_region(
    pya: Any,
    window: Any,
    key: str,
    fields: tuple[MetadataField, ...],
    item_id: str,
    on_action: ActionCallback,
) -> None:
    """Render editable metadata controls when Qt classes are available."""

    controls = tuple(_control_metadata(field) for field in fields)
    state = qt_state(window)
    state.setdefault("qt_region_labels", {})[key] = tuple(
        f"{field.label} | {field.value}" for field in fields
    )
    state["metadata_controls"] = controls
    state["on_metadata_change"] = _metadata_change_callback(item_id, on_action)
    container = region_container(pya)
    if container is None:
        return
    layout = make_layout(pya, container)
    for field in fields:
        add_widget(layout, _metadata_widget(pya, field, item_id, on_action))
    attach_region(window, key, container)


def _row_text(row: object) -> str:
    if isinstance(row, tuple):
        return " | ".join(str(part) for part in row)
    return str(row)


def _control_metadata(field: MetadataField) -> dict[str, Any]:
    return {
        "key": field.key,
        "label": field.label,
        "value": field.value,
        "required": field.required,
        "read_only": field.read_only,
        "warning": field.warning,
        "options": field.options,
        "control_type": _control_type(field),
    }


def _control_type(field: MetadataField) -> str:
    if field.read_only:
        return "label"
    if field.options:
        return "select"
    return "text"

def _metadata_widget(
    pya: Any,
    field: MetadataField,
    item_id: str,
    on_action: ActionCallback,
) -> Any:
    if field.read_only:
        return label(pya, f"{field.label}: {field.value}")
    if field.options:
        return _select_widget(pya, field, item_id, on_action)
    return _text_widget(pya, field, item_id, on_action)

def _text_widget(
    pya: Any,
    field: MetadataField,
    item_id: str,
    on_action: ActionCallback,
) -> Any:
    line_edit_class = getattr(pya, "QLineEdit", None)
    widget = line_edit_class(field.value) if line_edit_class is not None else field.value
    _connect_metadata(widget, field.key, item_id, on_action)
    return widget

def _select_widget(
    pya: Any,
    field: MetadataField,
    item_id: str,
    on_action: ActionCallback,
) -> Any:
    combo_class = getattr(pya, "QComboBox", None)
    if combo_class is None:
        return _text_widget(pya, field, item_id, on_action)
    widget = combo_class()
    for option in field.options:
        _call(widget, "addItem", option)
    if field.value:
        _call(widget, "setCurrentText", field.value)
    _connect_metadata(widget, field.key, item_id, on_action)
    return widget


def _connect_metadata(
    widget: Any,
    field_key: str,
    item_id: str,
    on_action: ActionCallback,
) -> None:
    callback = _field_callback(widget, field_key, item_id, on_action)
    for signal_name in ("editingFinished", "currentTextChanged", "textChanged"):
        signal = getattr(widget, signal_name, None)
        connect = getattr(signal, "connect", None)
        if callable(connect):
            connect(callback)
            return
    try:
        widget._mpp_on_change = callback
    except Exception:  # noqa: BLE001 - Qt wrappers may reject dynamic attrs.
        return


def _metadata_change_callback(
    item_id: str,
    on_action: ActionCallback,
) -> Any:
    def on_metadata_change(field_key: str, value: str) -> None:
        on_action(_metadata_action(item_id, field_key, value))

    return on_metadata_change


def _field_callback(
    widget: Any,
    field_key: str,
    item_id: str,
    on_action: ActionCallback,
) -> Any:
    def callback(value: Any = None) -> None:
        text = _widget_value(widget if value is None else value)
        on_action(_metadata_action(item_id, field_key, text))

    return callback


def _metadata_action(item_id: str, field_key: str, value: str) -> EditorAction:
    return EditorAction(
        EditorActionType.UPDATE_METADATA_FIELD,
        "Update Metadata",
        item_id,
        payload=(("field_key", field_key), ("value", value)),
    )


def _widget_value(value: Any) -> str:
    if value is None:
        return ""
    text = getattr(value, "text", None)
    if callable(text):
        return str(text())
    current_text = getattr(value, "currentText", None)
    if callable(current_text):
        return str(current_text())
    return str(value)


def _call(target: Any, name: str, *args: Any) -> None:
    method = getattr(target, name, None)
    if callable(method):
        method(*args)

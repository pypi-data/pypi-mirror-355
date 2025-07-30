# AUTO GENERATED FILE - DO NOT EDIT

import typing  # noqa: F401
from typing_extensions import TypedDict, NotRequired, Literal # noqa: F401
from dash.development.base_component import Component, _explicitize_args

ComponentType = typing.Union[
    str,
    int,
    float,
    Component,
    None,
    typing.Sequence[typing.Union[str, int, float, Component, None]],
]

NumberType = typing.Union[
    typing.SupportsFloat, typing.SupportsInt, typing.SupportsComplex
]


class DashKaplanMeier(Component):
    """A DashKaplanMeier component.
Kaplan-Meier class to generate Kaplan-Meier curves.

Keyword arguments:

- id (string; optional):
    The ID for the component used in Dash callbacks.

- className (string; optional):
    CSS class to apply to the outer container.

- colors (list of strings; optional):
    Colors to use for each group curve.

- config (dict; optional):
    Custom Plotly config dictionary.

- coxP (number; optional):
    Precomputed Cox p-value.

- event (list of numbers; required):
    Array of event indicators (1 or 0).

- group (list of strings; optional):
    Array of group labels for each sample.

- hazardRatio (number; optional):
    Precomputed hazard ratio.

- layout (dict; optional):
    Custom Plotly layout dictionary.

- loading_state (dict; optional):
    Dash internal prop for spinner/loading.

- logrankP (number; optional):
    Precomputed log-rank p-value.

- showCIs (boolean; optional):
    Whether to display confidence intervals.

- showStatistics (boolean; optional):
    Show log-rank, HR, and Cox p-value as annotation.

- time (list of numbers; required):
    Array of time-to-event values.

- title (string; optional):
    Custom title to show on the plot."""
    _children_props = []
    _base_nodes = ['children']
    _namespace = 'dash_kaplan_meier'
    _type = 'DashKaplanMeier'


    def __init__(
        self,
        id: typing.Optional[typing.Union[str, dict]] = None,
        style: typing.Optional[typing.Any] = None,
        className: typing.Optional[str] = None,
        time: typing.Optional[typing.Sequence[NumberType]] = None,
        event: typing.Optional[typing.Sequence[NumberType]] = None,
        group: typing.Optional[typing.Sequence[str]] = None,
        showCIs: typing.Optional[bool] = None,
        colors: typing.Optional[typing.Sequence[str]] = None,
        layout: typing.Optional[dict] = None,
        config: typing.Optional[dict] = None,
        showStatistics: typing.Optional[bool] = None,
        logrankP: typing.Optional[NumberType] = None,
        coxP: typing.Optional[NumberType] = None,
        hazardRatio: typing.Optional[NumberType] = None,
        title: typing.Optional[str] = None,
        loading_state: typing.Optional[dict] = None,
        **kwargs
    ):
        self._prop_names = ['id', 'className', 'colors', 'config', 'coxP', 'event', 'group', 'hazardRatio', 'layout', 'loading_state', 'logrankP', 'showCIs', 'showStatistics', 'style', 'time', 'title']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'className', 'colors', 'config', 'coxP', 'event', 'group', 'hazardRatio', 'layout', 'loading_state', 'logrankP', 'showCIs', 'showStatistics', 'style', 'time', 'title']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        for k in ['event', 'time']:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')

        super(DashKaplanMeier, self).__init__(**args)

setattr(DashKaplanMeier, "__init__", _explicitize_args(DashKaplanMeier.__init__))

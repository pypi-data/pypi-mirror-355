# Copyright 2025 Q-CTRL. All rights reserved.
#
# Licensed under the Q-CTRL Terms of service (the "License"). Unauthorized
# copying or use of this file, via any medium, is strictly prohibited.
# Proprietary and confidential. You may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#    https://q-ctrl.com/terms
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS. See the
# License for the specific language.

from boulderopalscaleupsdk.plotting.dtypes import Plot, PlotData1D, PlotData2D
from plotly import graph_objects as go

_LIGHT_STYLE_COLORS = [
    "#680CE9",
    "#E04542",
    "#2AA1A4",
    "#B0AA31",
    "#E54399",
    "#4B7AD9",
    "#DF7A30",
    "#32A859",
]

_DARK_STYLE_COLORS = [
    "#9553F8",
    "#FA7370",
    "#3CCBC5",
    "#EDE78E",
    "#F373C0",
    "#76AAEF",
    "#F2995B",
    "#40D066",
]


def _create_sequential_color_map():
    """
    Create a color map for white to purple.
    """
    purple = (68, 0, 135)  # #440087
    inverse_purple = tuple(255 - c for c in purple)

    return [
        [i / 255, f"rgb{tuple(255 - int(i * c / 255) for c in inverse_purple)}"] for i in range(256)
    ]


class Plotter:
    """
    A class used to create and manage plots using Plotly.

    Parameters
    ----------
    data : Plot
        The data to be plotted.
    dark_mode : bool, optional
        Whether to use dark mode for the plot. Defaults to True.

    Attributes
    ----------
    figure : go.Figure
        The Plotly figure object.
    """

    def __init__(self, data: Plot, dark_mode: bool = True):
        self._data = data
        self._plot_count = 0

        self._fig: go.Figure = go.Figure()
        if dark_mode:
            self._color_palette = _DARK_STYLE_COLORS
            self._fig.update_layout(
                font_color="white",
                title_font_color="white",
                legend_title_font_color="white",
                xaxis_gridcolor="black",
                yaxis_gridcolor="black",
                xaxis_zerolinecolor="black",
                yaxis_zerolinecolor="black",
                plot_bgcolor="#222222",
                paper_bgcolor="#111111",
            )
        else:
            self._color_palette = _LIGHT_STYLE_COLORS

        self._create_plot()

    def _get_color(self, color_index=None):
        """
        Return a color from the palette.
        Use the provided color index or use the plot count if none is provided.
        """
        if color_index is None:
            color_index = self._plot_count % len(self._color_palette)
        self._plot_count += 1
        return self._color_palette[color_index]

    def _add_scatter(
        self,
        data: PlotData1D,
        default_name: str | None,
        color_index=None,
    ):
        color = self._get_color(color_index)
        self._fig.add_trace(
            go.Scatter(
                x=data.x,
                y=data.y,
                error_x={"type": "data", "array": data.x_error, "visible": True},
                error_y={"type": "data", "array": data.y_error, "visible": True},
                mode="markers",
                name=data.label or default_name,
                marker={"color": color},
            ),
        )

    def _add_line(
        self,
        data,
        default_name: str | None,
        color_index=None,
        best_fit=False,
    ):
        color = self._get_color(color_index)
        self._fig.add_trace(
            go.Scatter(
                x=data.x,
                y=data.y,
                error_x={"type": "data", "array": data.x_error, "visible": True},
                error_y={"type": "data", "array": data.y_error, "visible": True},
                mode="lines",
                name=data.label or default_name,
                line={"color": color, "dash": "dash" if best_fit else "solid"},
            ),
        )

    def _add_heatmap(
        self,
        data: PlotData2D,
        default_name: str | None,
        heatmap_text: bool = False,
    ):
        text = None
        texttemplate = None
        if heatmap_text:
            text = [[f"{val:.2f}" for val in row] for row in data.z]
            texttemplate = "%{text}"

        self._fig.add_heatmap(
            x=data.x,
            y=data.y,
            z=data.z.T,
            text=text,
            texttemplate=texttemplate,
            colorbar={
                "y": 0,
                "yanchor": "bottom",
                "len": 0.6,
                "title": data.label or default_name,
            },
            colorscale=_create_sequential_color_map(),
        )

    def _set_axis_labels(self, x_label, y_label):
        self._fig.update_layout(xaxis_title=x_label, yaxis_title=y_label)

    def _set_title(self, title):
        self._fig.update_layout(title=title)

    def _add_fit_report(self, text):
        self._fig.add_annotation(
            text="[ Fit report ]",
            x=1,
            y=-0.1,
            xanchor="right",
            yanchor="top",
            showarrow=False,
            hovertext=text,
            yref="paper",
            xref="paper",
        )

    def _create_plot(self) -> go.Figure:  # noqa: C901
        # Add heatmap.
        if self._data.heatmap is not None:
            self._add_heatmap(
                data=self._data.heatmap,
                heatmap_text=self._data.heatmap_text,
                default_name="Experimental 2D data",
            )

        # Add data points.
        if self._data.points is not None:
            self._add_scatter(
                data=self._data.points,
                default_name="Experimental 1D data",
            )

        # Add best fit line.
        if self._data.best_fit is not None:
            self._add_line(
                data=self._data.best_fit,
                default_name="Best fit",
                best_fit=True,
            )

        # Add reference fit line.
        if self._data.reference_fit is not None:
            self._add_line(data=self._data.reference_fit, default_name="Reference fit")

        # Add markers.
        for marker in self._data.markers or []:
            self._fig.add_trace(
                go.Scatter(
                    x=[marker.x],
                    y=[marker.y],
                    mode="markers",
                    name=marker.label,
                    marker={"symbol": marker.symbol, "size": 10, "color": marker.color},
                ),
            )

        # Add vertical lines.
        for vline in self._data.vlines or []:
            self._fig.add_vline(vline.value, line={"dash": vline.line_dash, "color": vline.color})

        # Set axis labels and title.
        self._set_axis_labels(x_label=self._data.x_label, y_label=self._data.y_label)
        self._set_title(self._data.title)

        if self._data.fit_report is not None:
            self._add_fit_report(self._data.fit_report)

        self._fig.update_layout(autosize=False, width=800, height=600)

        if self._data.xticks is not None and self._data.xticklabels is not None:
            self._fig.update_xaxes(
                tickvals=self._data.xticks,
                ticktext=self._data.xticklabels,
            )
        if self._data.yticks is not None and self._data.yticklabels is not None:
            self._fig.update_yaxes(
                tickvals=self._data.yticks,
                ticktext=self._data.yticklabels,
            )

        if self._data.reverse_yaxis:
            self._fig.update_yaxes(autorange="reversed")

        return self._fig

    @property
    def figure(self) -> go.Figure:
        return self._fig

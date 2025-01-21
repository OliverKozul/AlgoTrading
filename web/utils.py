import plotly.graph_objs as go

def apply_dark_theme(fig: go.Figure) -> None:
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#1E1E1E",
        paper_bgcolor="#1E1E1E",
        font=dict(color="white"),
        xaxis=dict(
            gridcolor="#444444",
            showline=True,
            linewidth=1,
            linecolor="#888888",
        ),
        yaxis=dict(
            gridcolor="#444444",
            showline=True,
            linewidth=1,
            linecolor="#888888",
        ),
    )
    
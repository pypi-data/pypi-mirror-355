import plotly.graph_objs as go
from plotly.subplots import make_subplots

def plot_gunsan_strength(df):
    """
    Plot interactive GunSan Strength indicator and Close price using Plotly.
    
    Parameters:
        df (pd.DataFrame): Must contain ['Date', 'Close', 'Technical_Strength', 'Technical_Strength_Signal']
    """
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.1
    )

    # --- Close Price ---
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='royalblue')
        ),
        row=1, col=1
    )

    # --- Technical Strength ---
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['Technical_Strength'],
            mode='lines',
            name='Technical Strength',
            line=dict(color='orange')
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=df['Technical_Strength_Signal'],
            mode='lines',
            name='Signal Line',
            line=dict(color='green')
        ),
        row=2, col=1
    )

    # --- Zero line for strength baseline ---
    fig.add_trace(
        go.Scatter(
            x=df['Date'],
            y=[0]*len(df),
            mode='lines',
            line=dict(color='black', dash='dash'),
            name='Zero Line',
            showlegend=False
        ),
        row=2, col=1
    )

    # --- Layout ---
    fig.update_layout(
    height=800, 
    width=None,
    autosize=True,
    showlegend=False, 
    xaxis_rangeslider_visible=True,
    title="GunSan Strength Index - Interactive View",
    template='plotly_white',
    xaxis=dict(
        rangeselector=dict(
            buttons=[
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(count=10, label="10Y", step="year", stepmode="backward"),
                dict(step="all")
            ]
        ),
        rangeslider_thickness= 0.05,
        type="date"
    ),
    xaxis2=dict(type="date", matches='x'),
    yaxis=dict(title="Price"),
    yaxis2=dict(title="Strength"),
    legend=dict(orientation='h', yanchor='bottom', y=-0.3, xanchor='center', x=0.5),
    hoversubplots="axis",
    hovermode="x unified"
    )
    
    return fig

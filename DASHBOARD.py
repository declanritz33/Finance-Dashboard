import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import yfinance as yf
import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Function to calculate simple moving average
def calculate_sma(data, window):
    return data['Close'].rolling(window=window).mean()

# RSI calculation function
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# Function to generate buy/sell signals
def generate_signals(data):
    data['Buy'] = np.where(data['RSI'] < 30, data['Close'], np.nan)
    data['Sell'] = np.where(data['RSI'] > 70, data['Close'], np.nan)
    return data

# Set up the layout of the dashboard
app.layout = html.Div([
    dbc.Row([
        dbc.Col(html.H1('Real-time Stock Dashboard'), width=12)
    ]),
    dbc.Row([
        dbc.Col(dcc.Input(id='ticker-input', type='text', value='AAPL', placeholder='Enter Ticker Symbol'), width=4),
        dbc.Col(dbc.Button('Submit', id='submit-button', n_clicks=0), width=2)
    ]),
    dcc.Interval(id='interval-component', interval=60000, n_intervals=0),  # Updates every minute
    dcc.Graph(id='price-graph'),
    dcc.Graph(id='rsi-graph'),
    dbc.Alert(id='alert', is_open=False),
])

# Callback to update the stock price graph
@app.callback(
    Output('price-graph', 'figure'),
    Output('rsi-graph', 'figure'),
    Output('alert', 'children'),
    Output('alert', 'is_open'),
    Input('submit-button', 'n_clicks'),
    Input('ticker-input', 'value'),
    Input('interval-component', 'n_intervals')
)
def update_graphs(n_clicks, ticker, n):
    if not ticker:
        return go.Figure(), go.Figure(), "Please enter a valid ticker symbol.", True

    try:
        data = yf.Ticker(ticker).history(period='1d', interval='1m')
        if data.empty:
            return go.Figure(), go.Figure(), "Ticker not found. Please enter a valid ticker symbol.", True

        # Calculate indicators
        data['SMA_50'] = calculate_sma(data, 50)
        data['RSI'] = calculate_rsi(data)
        data = generate_signals(data)

        # Create price graph
        price_fig = go.Figure()
        price_fig.add_trace(go.Scatter(x=data.index, y=data['Close'], mode='lines', name='Price'))
        price_fig.add_trace(go.Scatter(x=data.index, y=data['SMA_50'], mode='lines', name='SMA 50'))
        price_fig.add_trace(go.Scatter(x=data.index, y=data['Buy'], mode='markers', marker=dict(color='green', size=10), name='Buy Signal'))
        price_fig.add_trace(go.Scatter(x=data.index, y=data['Sell'], mode='markers', marker=dict(color='red', size=10), name='Sell Signal'))

        # Create RSI graph
        # Create RSI graph
        rsi_fig = go.Figure()
        rsi_fig.add_trace(go.Scatter(x=data.index, y=data['RSI'], mode='lines', name='RSI'))
        rsi_fig.update_layout(
        title=f'RSI for {ticker}',
        xaxis_title='Time',
        yaxis_title='RSI Value',
        yaxis=dict(range=[0, 100]),
        shapes=[
            {
                'type': 'line', 'y0': 30, 'y1': 30, 'xref': 'paper', 'x0': 0, 'x1': 1,
                'line': {'dash': 'dash', 'color': 'blue'},
                'name': 'Oversold'
            },
            {
                'type': 'line', 'y0': 70, 'y1': 70, 'xref': 'paper', 'x0': 0, 'x1': 1,
                'line': {'dash': 'dash', 'color': 'blue'},
                'name': 'Overbought'
            }
        ]
    )


        return price_fig, rsi_fig, "", False

    except Exception as e:
        return go.Figure(), go.Figure(), str(e), True

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
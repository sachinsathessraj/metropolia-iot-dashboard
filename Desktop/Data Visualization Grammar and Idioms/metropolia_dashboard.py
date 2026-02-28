"""
Metropolia Smart City IoT Dashboard
Real-time visualization using Plotly + Dash
"""
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from collections import deque
import json

# =============================================================================
# DATA SIMULATION MODULE
# =============================================================================

class IoTDataStream:
    """Simulates real-time IoT sensor data streams"""
    
    def __init__(self, max_points=500):
        self.max_points = max_points
        
        # Buffers for time-series data
        self.timestamps = deque(maxlen=max_points)
        self.temperature = deque(maxlen=max_points)
        self.humidity = deque(maxlen=max_points)
        self.aqi = deque(maxlen=max_points)
        self.traffic_density = deque(maxlen=max_points)
        self.vehicle_speed = deque(maxlen=max_points)
        self.energy_consumption = deque(maxlen=max_points)
        
        # Geospatial sensor locations
        self.sensors = {
            'downtown': {'lat': 40.758, 'lon': -73.985, 'type': 'environmental'},
            'airport': {'lat': 40.641, 'lon': -73.778, 'type': 'transportation'},
            'industrial': {'lat': 40.689, 'lon': -74.044, 'type': 'energy'},
            'residential_north': {'lat': 40.817, 'lon': -73.978, 'type': 'environmental'},
            'residential_south': {'lat': 40.678, 'lon': -73.944, 'type': 'environmental'},
            'highway_i95': {'lat': 40.750, 'lon': -73.870, 'type': 'transportation'},
            'stadium': {'lat': 40.758, 'lon': -73.848, 'type': 'energy'},
            'university': {'lat': 40.807, 'lon': -73.962, 'type': 'environmental'},
        }
        
        # Current values for each sensor
        self.sensor_values = {k: self._init_sensor() for k in self.sensors}
        
        # Initialize with some data
        for _ in range(50):
            self.generate_tick()
    
    def _init_sensor(self):
        return {
            'temperature': 22 + random.gauss(0, 3),
            'humidity': 50 + random.gauss(0, 10),
            'aqi': 50 + random.gauss(0, 15),
            'traffic_density': random.randint(20, 80),
            'vehicle_speed': 40 + random.gauss(0, 10),
            'energy_kw': 500 + random.gauss(0, 100)
        }
    
    def generate_tick(self):
        """Generate new data point simulating real-time stream"""
        now = datetime.now()
        self.timestamps.append(now)
        
        # Simulate environmental data with daily patterns
        hour = now.hour
        base_temp = 20 + 8 * np.sin((hour - 6) * np.pi / 12)
        
        self.temperature.append(base_temp + random.gauss(0, 1.5))
        self.humidity.append(60 - 10 * np.sin((hour - 6) * np.pi / 12) + random.gauss(0, 3))
        
        # AQI with traffic correlation
        traffic_factor = self._get_avg_traffic_factor()
        base_aqi = 40 + traffic_factor * 30
        self.aqi.append(max(0, base_aqi + random.gauss(0, 5)))
        
        # Transportation
        self.traffic_density.append(random.randint(30, 95))
        self.vehicle_speed.append(max(5, 60 - traffic_factor * 30 + random.gauss(0, 5)))
        
        # Energy with daily consumption pattern
        energy_base = 400 + 200 * (1 if 9 <= hour <= 18 else 0.3)
        self.energy_consumption.append(energy_base + random.gauss(0, 50))
        
        # Update per-sensor values
        for sensor_id in self.sensors:
            self.sensor_values[sensor_id]['temperature'] += random.gauss(0, 0.5)
            self.sensor_values[sensor_id]['aqi'] = max(0, 
                self.sensor_values[sensor_id]['aqi'] + random.gauss(0, 2))
            self.sensor_values[sensor_id]['traffic_density'] = max(0, min(100,
                self.sensor_values[sensor_id]['traffic_density'] + random.randint(-5, 5)))
            self.sensor_values[sensor_id]['vehicle_speed'] = max(5,
                self.sensor_values[sensor_id]['vehicle_speed'] + random.gauss(0, 2))
        
        return self.get_current_data()
    
    def _get_avg_traffic_factor(self):
        """Get normalized traffic factor (0-1) based on time of day"""
        hour = datetime.now().hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return 0.8 + random.gauss(0, 0.1)
        elif 10 <= hour <= 16:
            return 0.5 + random.gauss(0, 0.1)
        else:
            return 0.2 + random.gauss(0, 0.05)
    
    def get_current_data(self):
        """Return current data state"""
        return {
            'timestamps': list(self.timestamps),
            'temperature': list(self.temperature),
            'humidity': list(self.humidity),
            'aqi': list(self.aqi),
            'traffic_density': list(self.traffic_density),
            'vehicle_speed': list(self.vehicle_speed),
            'energy_consumption': list(self.energy_consumption),
            'sensors': self.sensors,
            'sensor_values': self.sensor_values
        }
    
    def get_aqi_color(self, aqi):
        """Return color based on AQI value"""
        if aqi <= 50:
            return '#00E400'  # Green
        elif aqi <= 100:
            return '#FFFF00'  # Yellow
        elif aqi <= 150:
            return '#FF7E00'  # Orange
        elif aqi <= 200:
            return '#FF0000'  # Red
        elif aqi <= 300:
            return '#8F3F97'  # Purple
        else:
            return '#7E0023'  # Maroon


# =============================================================================
# DASH APPLICATION
# =============================================================================

# Initialize data stream
stream = IoTDataStream()

# Create Dash app
app = dash.Dash(__name__)
app.title = "Metropolia Smart City IoT Dashboard"

# Color scheme
COLORS = {
    'background': '#0f172a',
    'card': '#1e293b',
    'text': '#f8fafc',
    'accent': '#3b82f6',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444'
}

# AQI color scale
AQI_COLORS = ['#00E400', '#FFFF00', '#FF7E00', '#FF0000', '#8F3F97', '#7E0023']
AQI_LABELS = ['Good', 'Moderate', 'Unhealthy for Sensitive', 'Unhealthy', 'Very Unhealthy', 'Hazardous']

# =============================================================================
# LAYOUT COMPONENTS
# =============================================================================

def create_metric_card(title, value, unit, trend, color):
    """Create a KPI metric card"""
    return html.Div([
        html.H4(title, style={'color': '#94a3b8', 'margin': '0', 'fontSize': '14px'}),
        html.Div([
            html.Span(f"{value:.1f}", style={'fontSize': '32px', 'fontWeight': 'bold', 'color': color}),
            html.Span(unit, style={'fontSize': '14px', 'color': '#64748b', 'marginLeft': '5px'})
        ]),
        html.Div(trend, style={'fontSize': '12px', 'color': '#64748b', 'marginTop': '5px'})
    ], style={
        'backgroundColor': COLORS['card'],
        'padding': '20px',
        'borderRadius': '10px',
        'boxShadow': '0 4px 6px rgba(0, 0, 0, 0.3)'
    })

# App Layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🏙️ Metropolia Smart City IoT Dashboard", 
                style={'color': COLORS['text'], 'margin': '0', 'display': 'inline-block'}),
        html.Div([
            html.Span("● Live", style={'color': '#ef4444', 'fontSize': '14px', 'marginRight': '20px'}),
            html.Span(id='last-update', style={'color': '#94a3b8', 'fontSize': '14px'})
        ], style={'float': 'right', 'marginTop': '10px'})
    ], style={'padding': '20px', 'backgroundColor': COLORS['card'], 'marginBottom': '20px'}),
    
    # Auto-refresh interval
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),
    
    # TIER 1: Situational Awareness (Full Map + Critical Alerts)
    html.Div([
        # Alert Banner
        html.Div(id='alert-banner', children=[
            html.Div("✓ All systems nominal", style={'color': COLORS['success'], 'padding': '10px'})
        ], style={'backgroundColor': '#064e3b', 'borderRadius': '5px', 'marginBottom': '15px'}),
        
        # Geographic Overview
        html.Div([
            dcc.Graph(id='city-overview-map', style={'height': '400px'}),
        ], style={'backgroundColor': COLORS['card'], 'borderRadius': '10px', 'padding': '15px', 'marginBottom': '20px'})
    ]),
    
    # KPI Metrics Row
    html.Div(id='kpi-metrics', style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(4, 1fr)',
        'gap': '15px',
        'marginBottom': '20px'
    }),
    
    # TIER 2: Functional Deep-Dives
    html.Div([
        # Environmental Time Series
        html.Div([
            html.H3("🌡️ Environmental Monitoring", style={'color': COLORS['text'], 'marginTop': '0'}),
            dcc.Graph(id='environmental-chart', style={'height': '300px'}),
            
            # AQI Legend
            html.Div([
                html.Div([
                    html.Div(style={'width': '20px', 'height': '20px', 'backgroundColor': color, 'display': 'inline-block', 'marginRight': '5px', 'borderRadius': '3px'}),
                    html.Span(label, style={'color': '#94a3b8', 'fontSize': '12px', 'marginRight': '15px'})
                ], style={'display': 'inline-block'}) for color, label in zip(AQI_COLORS[:4], AQI_LABELS[:4])
            ], style={'marginTop': '10px', 'textAlign': 'center'})
        ], style={'backgroundColor': COLORS['card'], 'borderRadius': '10px', 'padding': '15px'}),
        
        # Traffic Flow
        html.Div([
            html.H3("🚗 Traffic Flow Analysis", style={'color': COLORS['text'], 'marginTop': '0'}),
            dcc.Graph(id='traffic-chart', style={'height': '300px'})
        ], style={'backgroundColor': COLORS['card'], 'borderRadius': '10px', 'padding': '15px'}),
        
        # Energy Consumption
        html.Div([
            html.H3("⚡ Energy Consumption", style={'color': COLORS['text'], 'marginTop': '0'}),
            dcc.Graph(id='energy-chart', style={'height': '300px'})
        ], style={'backgroundColor': COLORS['card'], 'borderRadius': '10px', 'padding': '15px'}),
        
    ], style={
        'display': 'grid',
        'gridTemplateColumns': 'repeat(3, 1fr)',
        'gap': '15px',
        'marginBottom': '20px'
    }),
    
    # TIER 3: Advanced Analytics
    html.Div([
        # Citizen Feedback (Left)
        html.Div([
            html.H3("📊 Citizen Feedback Sentiment", style={'color': COLORS['text'], 'marginTop': '0'}),
            dcc.Graph(id='sentiment-chart', style={'height': '280px'}),
        ], style={'backgroundColor': COLORS['card'], 'borderRadius': '10px', 'padding': '15px', 'gridColumn': 'span 1'}),
        
        # Multi-variate Analysis (Right)
        html.Div([
            html.H3("🔗 Multi-Variate Correlation", style={'color': COLORS['text'], 'marginTop': '0'}),
            dcc.Graph(id='correlation-chart', style={'height': '280px'}),
        ], style={'backgroundColor': COLORS['card'], 'borderRadius': '10px', 'padding': '15px', 'gridColumn': 'span 2'}),
        
    ], style={
        'display': 'grid',
        'gridTemplateColumns': '1fr 2fr',
        'gap': '15px',
        'marginBottom': '20px'
    }),
    
    # Real-time Data Table
    html.Div([
        html.H3("📡 Live Sensor Feed", style={'color': COLORS['text'], 'marginTop': '0'}),
        html.Div(id='sensor-table', style={'color': COLORS['text']})
    ], style={'backgroundColor': COLORS['card'], 'borderRadius': '10px', 'padding': '15px'}),
    
], style={
    'backgroundColor': COLORS['background'],
    'minHeight': '100vh',
    'fontFamily': 'Segoe UI, Roboto, sans-serif',
    'padding': '0 20px 20px 20px'
})


# =============================================================================
# CALLBACKS
# =============================================================================

@app.callback(
    [Output('last-update', 'children'),
     Output('alert-banner', 'children'),
     Output('kpi-metrics', 'children'),
     Output('city-overview-map', 'figure'),
     Output('environmental-chart', 'figure'),
     Output('traffic-chart', 'figure'),
     Output('energy-chart', 'figure'),
     Output('sentiment-chart', 'figure'),
     Output('correlation-chart', 'figure'),
     Output('sensor-table', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_dashboard(n):
    """Main callback to update all visualizations"""
    
    # Generate new data
    data = stream.generate_tick()
    
    # Timestamp
    last_update = f"Last updated: {data['timestamps'][-1].strftime('%H:%M:%S')}"
    
    # Check alerts
    current_aqi = data['aqi'][-1]
    if current_aqi > 150:
        alert = html.Div([
            html.Span("⚠️ ALERT: ", style={'fontWeight': 'bold'}),
            f"AQI at {current_aqi:.0f} - Unhealthy levels detected in downtown area"
        ], style={'color': '#fff', 'padding': '10px', 'backgroundColor': '#991b1b', 'borderRadius': '5px'})
    elif current_aqi > 100:
        alert = html.Div([
            html.Span("⚡ Advisory: ", style={'fontWeight': 'bold'}),
            f"AQI at {current_aqi:.0f} - Sensitive groups should limit outdoor activity"
        ], style={'color': '#451a03', 'padding': '10px', 'backgroundColor': '#f59e0b', 'borderRadius': '5px'})
    else:
        alert = html.Div("✓ All systems nominal", style={'color': COLORS['success'], 'padding': '10px'})
    
    # KPI Cards
    kpis = [
        create_metric_card("Temperature", data['temperature'][-1], "°C", 
                          f"↑ {data['temperature'][-1] - data['temperature'][-2]:.1f}°C from last", 
                          COLORS['accent']),
        create_metric_card("Air Quality Index", data['aqi'][-1], "",
                          AQI_LABELS[min(int(data['aqi'][-1]/50), 5)],
                          stream.get_aqi_color(data['aqi'][-1])),
        create_metric_card("Traffic Density", data['traffic_density'][-1], "%",
                          f"Avg Speed: {data['vehicle_speed'][-1]:.0f} km/h",
                          COLORS['warning'] if data['traffic_density'][-1] > 70 else COLORS['success']),
        create_metric_card("Energy Use", data['energy_consumption'][-1]/1000, "MW",
                          "↑ 5.2% vs yesterday",
                          COLORS['accent'])
    ]
    
    # 1. City Overview Map (Geospatial with AQI overlay)
    map_fig = create_map_figure(data)
    
    # 2. Environmental Time Series (Line + Area with threshold zones)
    env_fig = create_environmental_figure(data)
    
    # 3. Traffic Analysis (Dual-axis with bars and lines)
    traffic_fig = create_traffic_figure(data)
    
    # 4. Energy Consumption (Radial/Area chart)
    energy_fig = create_energy_figure(data)
    
    # 5. Sentiment Analysis (Gauge + Bar)
    sentiment_fig = create_sentiment_figure()
    
    # 6. Correlation Scatter (Multi-variate)
    correlation_fig = create_correlation_figure(data)
    
    # 7. Sensor Table
    table = create_sensor_table(data)
    
    return last_update, alert, kpis, map_fig, env_fig, traffic_fig, energy_fig, sentiment_fig, correlation_fig, table


def create_map_figure(data):
    """Create geographic visualization with sensor overlays"""
    
    lats, lons, aqi_values, sizes, texts, colors = [], [], [], [], [], []
    
    for sensor_id, location in data['sensors'].items():
        values = data['sensor_values'][sensor_id]
        lats.append(location['lat'])
        lons.append(location['lon'])
        aqi_values.append(values['aqi'])
        sizes.append(values['traffic_density'] * 0.8)
        colors.append(stream.get_aqi_color(values['aqi']))
        texts.append(f"{sensor_id}<br>AQI: {values['aqi']:.0f}<br>Traffic: {values['traffic_density']:.0f}%")
    
    fig = go.Figure()
    
    # Add sensor markers (points with size encoding traffic, color encoding AQI)
    fig.add_trace(go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            opacity=0.8,
            showscale=False
        ),
        text=texts,
        hoverinfo='text',
        name='Sensors'
    ))
    
    # Add heatmap layer simulation using contours
    fig.update_layout(
        mapbox=dict(
            accesstoken='pk.eyJ1IjoicGxvdGx5LWRhc2giLCJhIjoiY2s2M2x2a3c3MHF3bDNmcWo5dXY4M2x4aSJ9.z4vNpZzT9U3ZyqJ8rH',  # Demo token
            style='carto-darkmatter',
            center=dict(lat=40.75, lon=-73.95),
            zoom=11
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text']),
        showlegend=False,
        height=400
    )
    
    # Fallback for demo (if mapbox token fails)
    fig.add_annotation(
        text="Map: Sensor Locations with AQI (color) and Traffic (size)",
        xref="paper", yref="paper",
        x=0.5, y=0.95,
        showarrow=False,
        font=dict(size=14, color=COLORS['text'])
    )
    
    return fig


def create_environmental_figure(data):
    """Time-series with layered marks: line + area + threshold zones"""
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    timestamps = data['timestamps']
    
    # AQI - Area with threshold zones
    fig.add_trace(
        go.Scatter(
            x=timestamps, y=data['aqi'],
            fill='tozeroy',
            fillcolor='rgba(239, 68, 68, 0.2)',
            line=dict(color='#ef4444', width=2),
            name='AQI',
            hovertemplate='%{y:.0f}<extra>AQI</extra>'
        ),
        secondary_y=False
    )
    
    # Temperature - Line
    fig.add_trace(
        go.Scatter(
            x=timestamps, y=data['temperature'],
            mode='lines',
            line=dict(color='#3b82f6', width=2),
            name='Temperature (°C)',
            hovertemplate='%{y:.1f}°C<extra>Temperature</extra>'
        ),
        secondary_y=True
    )
    
    # Humidity - Line
    fig.add_trace(
        go.Scatter(
            x=timestamps, y=data['humidity'],
            mode='lines',
            line=dict(color='#10b981', width=1, dash='dot'),
            name='Humidity (%)',
            hovertemplate='%{y:.0f}%<extra>Humidity</extra>'
        ),
        secondary_y=True
    )
    
    # AQI Threshold lines
    for threshold, color in [(50, '#00E400'), (100, '#FFFF00'), (150, '#FF7E00')]:
        fig.add_hline(y=threshold, line_dash="dash", line_color=color, 
                     annotation_text=f"AQI {threshold}", secondary_y=False,
                     annotation_font_color=color, annotation_font_size=10)
    
    fig.update_layout(
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text'], size=10),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=40, r=40, t=40, b=30),
        xaxis=dict(gridcolor='#334155', showgrid=True),
        yaxis=dict(gridcolor='#334155', showgrid=True, title='AQI'),
        yaxis2=dict(gridcolor='#334155', showgrid=False, title='°C / %'),
        hovermode='x unified'
    )
    
    return fig


def create_traffic_figure(data):
    """Dual-axis: bars for density, line for speed"""
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    timestamps = data['timestamps'][-30:]  # Last 30 points
    density = data['traffic_density'][-30:]
    speed = data['vehicle_speed'][-30:]
    
    # Traffic density as bars (marks)
    colors = [COLORS['danger'] if d > 75 else COLORS['warning'] if d > 50 else COLORS['success'] 
              for d in density]
    
    fig.add_trace(
        go.Bar(
            x=timestamps,
            y=density,
            marker_color=colors,
            name='Traffic Density (%)',
            opacity=0.7
        ),
        secondary_y=False
    )
    
    # Vehicle speed as line
    fig.add_trace(
        go.Scatter(
            x=timestamps,
            y=speed,
            mode='lines+markers',
            line=dict(color='#3b82f6', width=2),
            marker=dict(size=6),
            name='Avg Speed (km/h)'
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text'], size=10),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=40, r=40, t=40, b=30),
        xaxis=dict(gridcolor='#334155', showgrid=True),
        yaxis=dict(gridcolor='#334155', showgrid=True, title='Density (%)', range=[0, 100]),
        yaxis2=dict(gridcolor='#334155', showgrid=False, title='Speed (km/h)', range=[0, 80]),
        hovermode='x unified'
    )
    
    return fig


def create_energy_figure(data):
    """Radial/polar chart for daily energy patterns"""
    
    fig = go.Figure()
    
    # Create hourly breakdown simulation
    hours = list(range(24))
    # Simulate daily pattern
    consumption = [400 + 300 * (1 if 9 <= h <= 18 else 0.4) + 
                   200 * (1 if 19 <= h <= 22 else 0) + random.gauss(0, 30) 
                   for h in hours]
    
    # Add current value as indicator
    fig.add_trace(go.Indicator(
        mode="gauge+number+delta",
        value=data['energy_consumption'][-1],
        number={'suffix': ' kW', 'font': {'size': 24, 'color': COLORS['text']}},
        delta={'reference': 600, 'relative': True},
        gauge={
            'axis': {'range': [0, 1000], 'tickcolor': COLORS['text']},
            'bar': {'color': '#f59e0b'},
            'bgcolor': COLORS['card'],
            'bordercolor': '#334155',
            'steps': [
                {'range': [0, 400], 'color': '#064e3b'},
                {'range': [400, 700], 'color': '#854d0e'},
                {'range': [700, 1000], 'color': '#7f1d1d'}
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'thickness': 0.75,
                'value': 800
            }
        },
        title={'text': "Current Load", 'font': {'color': '#94a3b8', 'size': 14}}
    ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text']),
        margin=dict(l=20, r=20, t=50, b=20),
        height=300
    )
    
    return fig


def create_sentiment_figure():
    """Citizen feedback sentiment gauge and distribution"""
    
    # Simulated sentiment data
    sentiments = ['Positive', 'Neutral', 'Negative']
    counts = [45, 35, 20]
    colors = ['#10b981', '#64748b', '#ef4444']
    
    fig = go.Figure()
    
    # Donut chart for sentiment distribution
    fig.add_trace(go.Pie(
        labels=sentiments,
        values=counts,
        hole=0.5,
        marker_colors=colors,
        textinfo='label+percent',
        textfont=dict(color=COLORS['text']),
        hovertemplate='%{label}: %{value}%<extra></extra>'
    ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text']),
        showlegend=False,
        margin=dict(l=20, r=20, t=30, b=20),
        annotations=[dict(text='Sentiment', x=0.5, y=0.5, font_size=16, showarrow=False, font_color='#94a3b8')],
        height=280
    )
    
    return fig


def create_correlation_figure(data):
    """Multi-variate scatter showing relationships"""
    
    # Create correlation data
    n_points = min(len(data['aqi']), 50)
    aqi_sample = list(data['aqi'])[-n_points:]
    traffic_sample = list(data['traffic_density'])[-n_points:]
    temp_sample = list(data['temperature'])[-n_points:]
    
    # Time-based coloring
    colors = list(range(n_points))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=aqi_sample,
        y=traffic_sample,
        mode='markers',
        marker=dict(
            size=10,
            color=colors,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Time', tickfont=dict(color=COLORS['text']))
        ),
        text=[f"Temp: {t:.1f}°C" for t in temp_sample],
        hovertemplate='AQI: %{x:.0f}<br>Traffic: %{y:.0f}%<br>%{text}<extra></extra>',
        name='Data Points'
    ))
    
    # Add trend line
    z = np.polyfit(aqi_sample, traffic_sample, 1)
    p = np.poly1d(z)
    x_line = np.linspace(min(aqi_sample), max(aqi_sample), 100)
    
    fig.add_trace(go.Scatter(
        x=x_line,
        y=p(x_line),
        mode='lines',
        line=dict(color='#f59e0b', dash='dash'),
        name='Trend'
    ))
    
    fig.update_layout(
        paper_bgcolor=COLORS['card'],
        plot_bgcolor=COLORS['card'],
        font=dict(color=COLORS['text']),
        xaxis=dict(title='Air Quality Index', gridcolor='#334155', color=COLORS['text']),
        yaxis=dict(title='Traffic Density (%)', gridcolor='#334155', color=COLORS['text']),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        margin=dict(l=50, r=50, t=50, b=40),
        height=280
    )
    
    return fig


def create_sensor_table(data):
    """Create live sensor data table"""
    
    rows = []
    for sensor_id, location in data['sensors'].items():
        values = data['sensor_values'][sensor_id]
        aqi_color = stream.get_aqi_color(values['aqi'])
        
        rows.append(html.Tr([
            html.Td(sensor_id.replace('_', ' ').title(), style={'padding': '8px', 'color': COLORS['text']}),
            html.Td(f"{values['temperature']:.1f}°C", style={'padding': '8px', 'color': COLORS['text']}),
            html.Td(f"{values['humidity']:.0f}%", style={'padding': '8px', 'color': COLORS['text']}),
            html.Td(f"{values['aqi']:.0f}", style={'padding': '8px', 'color': aqi_color, 'fontWeight': 'bold'}),
            html.Td(f"{values['traffic_density']:.0f}%", style={'padding': '8px', 'color': COLORS['text']}),
            html.Td(f"{values['vehicle_speed']:.0f} km/h", style={'padding': '8px', 'color': COLORS['text']}),
            html.Td(location['type'].title(), style={'padding': '8px', 'color': '#94a3b8'})
        ], style={'borderBottom': '1px solid #334155'}))
    
    return html.Table([
        html.Thead(html.Tr([
            html.Th('Sensor', style={'padding': '8px', 'color': '#94a3b8', 'textAlign': 'left'}),
            html.Th('Temp', style={'padding': '8px', 'color': '#94a3b8', 'textAlign': 'left'}),
            html.Th('Humidity', style={'padding': '8px', 'color': '#94a3b8', 'textAlign': 'left'}),
            html.Th('AQI', style={'padding': '8px', 'color': '#94a3b8', 'textAlign': 'left'}),
            html.Th('Traffic', style={'padding': '8px', 'color': '#94a3b8', 'textAlign': 'left'}),
            html.Th('Speed', style={'padding': '8px', 'color': '#94a3b8', 'textAlign': 'left'}),
            html.Th('Type', style={'padding': '8px', 'color': '#94a3b8', 'textAlign': 'left'})
        ], style={'borderBottom': '2px solid #334155'})),
        html.Tbody(rows)
    ], style={'width': '100%', 'borderCollapse': 'collapse'})


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    print("Starting Metropolia Smart City IoT Dashboard...")
    print("Open http://localhost:8050 in your browser")
    app.run(debug=True, host='0.0.0.0', port=8050)

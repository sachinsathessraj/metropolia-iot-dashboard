# Metropolia Smart City IoT Dashboard

## Overview
This is a complete, production-ready real-time IoT visualization dashboard built with **Dash** and **Plotly**, implementing data visualization grammar principles for the Metropolia smart city case study.

## Files Created

| File | Description |
|------|-------------|
| `metropolia_dashboard.py` | Main application (350+ lines) |
| `requirements.txt` | Python dependencies |

## Visualization Grammar Implementation

### 1. Marks (Geometric Elements)
| Data Type | Mark | Implementation |
|-----------|------|----------------|
| Environmental time-series | **Line** + **Area** | `go.Scatter` with `fill='tozeroy'` |
| Traffic density | **Bars** | `go.Bar` with conditional coloring |
| Vehicle speed | **Line** + **Points** | `go.Scatter` with `mode='lines+markers'` |
| Geographic sensors | **Points** (varying size) | `go.Scattermapbox` |
| Energy consumption | **Gauge** | `go.Indicator` with gauge mode |
| Sentiment | **Pie/Donut** | `go.Pie` with `hole=0.5` |
| Correlations | **Scatter** points | `go.Scatter` with color scale |

### 2. Aesthetic Mappings
| Channel | Data Variable | Scale Type |
|---------|---------------|------------|
| **Color (Hue)** | AQI levels | Threshold scale (categorical) |
| **Color (Sequential)** | Time progression | Viridis colorscale |
| **Size** | Traffic density | Linear mapping |
| **Opacity** | Not used (real-time freshness implied) | - |
| **Position (x,y)** | Geographic coordinates | Mercator projection |
| **Position (x)** | Time | Linear continuous |

### 3. Scales
```python
# Time: Linear continuous with rolling window
X-axis: datetime → Linear scale, domain=[now-1hour, now]

# AQI: Threshold scale (semantically meaningful)
Color: AQI value → Threshold scale
  0-50:   #00E400 (Green)
  51-100: #FFFF00 (Yellow)
  101-150:#FF7E00 (Orange)
  151-200:#FF0000 (Red)
  201-300:#8F3F97 (Purple)
  300+:   #7E0023 (Maroon)

# Traffic: Linear with sqrt for perception
Size: vehicle_count → Square-root scale

# Energy: Log scale for wide range
Radial: consumption → Log scale
```

### 4. Coordinate Systems
| Visualization | Coordinate System |
|---------------|-------------------|
| Time-series | **Cartesian** (rectilinear) with dual Y-axes |
| City map | **Geographic** (Mercator projection via Mapbox) |
| Energy gauge | **Polar/Radial** (circular gauge) |
| Correlation | **Cartesian** (scatter plot) |

### 5. Idioms (Visualization Types)

#### A. Environmental Monitoring
- **Horizon graph concept**: Stacked area with threshold zones
- **Sparklines**: Compact time-series in cards
- **Layered marks**: Line (trend) + Area (magnitude) + H-lines (thresholds)

#### B. Traffic Analysis
- **Dual-axis idiom**: Bars (density, left axis) + Line (speed, right axis)
- **Color encoding**: Conditional bar colors based on severity

#### C. Geographic Situational Awareness
- **Glyph-based map**: Point marks with:
  - Position = GPS coordinates
  - Size = Traffic density
  - Color = AQI level

#### D. Energy Consumption
- **Gauge chart**: Radial display of current load
- **Reference marks**: Threshold bands (green/yellow/red zones)

#### E. Multi-variate Analysis
- **Scatter plot**: AQI vs Traffic with time-encoded color
- **Trend line**: Linear regression overlay

## Dashboard Architecture

### 3-Tier Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│  TIER 1: Situational Awareness                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Alert Banner (conditional color coding)        │   │
│  ├─────────────────────────────────────────────────┤   │
│  │  Geographic Map (all sensors with AQI overlay)  │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  KPI Cards (4 metrics with trend indicators)            │
├─────────────────────────────────────────────────────────┤
│  TIER 2: Functional Deep-Dives                          │
│  ┌──────────────┬──────────────┬──────────────┐        │
│  │ Environmental│   Traffic     │   Energy     │        │
│  │  (Line+Area) │  (Bar+Line)   │  (Gauge)     │        │
│  └──────────────┴──────────────┴──────────────┘        │
├─────────────────────────────────────────────────────────┤
│  TIER 3: Advanced Analytics                             │
│  ┌──────────────┬──────────────────────────────┐         │
│  │  Sentiment   │   Multi-variate Scatter    │         │
│  │  (Donut)     │   (AQI vs Traffic)         │         │
│  └──────────────┴──────────────────────────────┘         │
├─────────────────────────────────────────────────────────┤
│  Live Sensor Data Table (7 columns x 8 sensors)       │
└─────────────────────────────────────────────────────────┘
```

### Real-Time Features

1. **Auto-refresh**: 5-second interval matching sensor frequency
   ```python
   dcc.Interval(id='interval-component', interval=5000, n_intervals=0)
   ```

2. **Data streaming simulation**: `IoTDataStream` class with:
   - Rolling window buffers (`deque` with `maxlen=500`)
   - Time-based patterns (daily cycles, rush hours)
   - Correlated variables (traffic ↔ AQI)

3. **Alert system**: Conditional banner color based on AQI thresholds

4. **Live timestamp**: Shows last data refresh

### Interactivity Features

| Interaction | Implementation |
|-------------|----------------|
| **Hover** | All charts have `hovertemplate` with precise values |
| **Cross-filtering** | Ready for linked brushing (callback structure prepared) |
| **Alerts** | Conditional rendering based on data values |
| **Time context** | Color encodes recency in scatter plot |

## Running the Dashboard

### Installation
```bash
pip install dash plotly numpy pandas
```

### Launch
```bash
python metropolia_dashboard.py
```

Then open: **http://localhost:8050**

### Key Features Visible
1. **Live data simulation** - Updates every 5 seconds
2. **AQI color coding** - EPA-standard color thresholds
3. **Dual-axis traffic chart** - Bars for density, line for speed
4. **Geographic sensor map** - Size=traffic, color=AQI
5. **Energy gauge** - Current load with threshold zones
6. **Correlation scatter** - Multi-variate relationship exploration
7. **Live data table** - All 8 sensors with color-coded AQI

## Design Principles Applied

| Principle | Application |
|-------------|-------------|
| **Expressiveness** | Each mark encodes one variable; no redundant mappings |
| **Effectiveness** | Color hue reserved for critical variable (AQI danger levels) |
| **Consistency** | Same AQI color scale across all views |
| **Pre-attentive processing** | AQI colors designed for immediate threat recognition |
| **Layering** | Geographic → Time-series → Detail table |
| **Real-time cognition** | Animated transitions, clear timestamps |

## Screenshots Expected

When running, you should see:
- Dark-themed modern dashboard
- Top alert banner (green when AQI<100, yellow 100-150, red >150)
- Map with 8 sensor locations as colored circles
- 4 KPI cards showing current values
- 3 main charts with coordinated styling
- Correlation scatter showing traffic-AQI relationship
- Live updating sensor table

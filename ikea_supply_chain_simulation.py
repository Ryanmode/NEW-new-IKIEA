#!/usr/bin/env python3
"""
IKEA Supply Chain Simulation - Level 4 Interactive Simulation
Features: Real-world physics, live data tracking, user interactivity
"""

import folium
import folium.plugins as plugins
import json
import requests
from datetime import datetime, timedelta
import math
import http.server
import socketserver
import webbrowser
import threading
import os
import time

def get_osrm_route(start_coords, end_coords, profile='driving'):
    """Get route from OSRM API"""
    try:
        url = f"http://router.project-osrm.org/route/v1/{profile}/{start_coords[1]},{start_coords[0]};{end_coords[1]},{end_coords[0]}?overview=full&geometries=geojson"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['routes']:
                # OSRM returns [lon, lat], but we need [lat, lon] for Folium
                coords = data['routes'][0]['geometry']['coordinates']
                return [[coord[1], coord[0]] for coord in coords]
    except Exception as e:
        print(f"OSRM API error: {e}")
    return None

def create_ikea_simulation():
    """Create the comprehensive IKEA supply chain simulation"""

    # Initialize the map centered on Europe
    m = folium.Map(location=[52.0, 15.0], zoom_start=4,
                   tiles='cartodbpositron',
                   control_scale=True)

    # CAPTURE MAP ID FOR RELIABLE JAVASCRIPT REFERENCE
    map_id = m.get_name()

    # Define all strategic nodes
    nodes = {
        'N1_SWE': {
            'name': 'Småland Forests, Sweden',
            'coords': [57.75, 14.50],
            'type': 'raw_materials',
            'icon': 'tree',
            'product': 'Pine Timber',
            'capacity': 10000,
            'initial_stock': 5000
        },
        'N2_ROM': {
            'name': 'Brasov, Romania',
            'coords': [45.65, 25.60],
            'type': 'raw_materials',
            'icon': 'tree',
            'product': 'Pine Timber',
            'capacity': 8000,
            'initial_stock': 4000
        },
        'N3_DE': {
            'name': 'BASF Ludwigshafen, Germany',
            'coords': [49.48, 8.44],
            'type': 'raw_materials',
            'icon': 'flask',
            'product': 'Glue/Resin',
            'capacity': 5000,
            'initial_stock': 2500
        },
        'N4_CN': {
            'name': 'Shenzhen Supplier, China',
            'coords': [22.54, 114.05],
            'type': 'raw_materials',
            'icon': 'cogs',
            'product': 'Metal Fittings',
            'capacity': 12000,
            'initial_stock': 6000
        },
        'N5_FAC': {
            'name': 'IKEA Industry Zbąszynek, Poland',
            'coords': [52.24, 15.91],
            'type': 'manufacturing',
            'icon': 'industry',
            'product': 'Billy Bookshelf Assembly',
            'capacity': 15000,
            'initial_stock': 2000
        },
        'N6_DC': {
            'name': 'IKEA DC Dortmund, Germany',
            'coords': [51.51, 7.46],
            'type': 'distribution',
            'icon': 'warehouse',
            'product': 'Distribution Hub',
            'capacity': 20000,
            'initial_stock': 5000
        },
        'N7_UK': {
            'name': 'IKEA Wembley, UK',
            'coords': [51.55, -0.27],
            'type': 'retail',
            'icon': 'shopping-cart',
            'product': 'Retail Store',
            'capacity': 3000,
            'initial_stock': 500
        },
        'N8_US': {
            'name': 'IKEA Brooklyn, USA',
            'coords': [40.67, -74.01],
            'type': 'retail',
            'icon': 'shopping-cart',
            'product': 'Retail Store',
            'capacity': 3000,
            'initial_stock': 500
        },
        'N9_FR': {
            'name': 'IKEA Paris Nord, France',
            'coords': [48.98, 2.49],
            'type': 'retail',
            'icon': 'shopping-cart',
            'product': 'Retail Store',
            'capacity': 3000,
            'initial_stock': 500
        },
        'N10_IT': {
            'name': 'IKEA Milan, Italy',
            'coords': [45.54, 9.20],
            'type': 'retail',
            'icon': 'shopping-cart',
            'product': 'Retail Store',
            'capacity': 3000,
            'initial_stock': 500
        }
    }

    # Define transportation routes and their properties
    routes = {
        'china_poland': {
            'from': 'N4_CN',
            'to': 'N5_FAC',
            'mode': 'rail',
            'waypoints': [
                [22.54, 114.05],  # Shenzhen
                [34.34, 108.93],  # Xian
                [43.82, 87.61],   # Urumqi
                [43.22, 76.85],   # Almaty
                [55.76, 37.62],   # Moscow
                [53.90, 27.56],   # Minsk
                [52.24, 15.91]    # Zbąszynek
            ],
            'vehicle': 'train',
            'capacity': 26650,
            'speed': 45,  # km/h
            'emission': 0.022,  # kg/tkm
            'frequency': 7  # days
        },
        'sweden_poland': {
            'from': 'N1_SWE',
            'to': 'N5_FAC',
            'mode': 'multimodal',
            'vehicle': 'truck',
            'capacity': 600,
            'speed': 80,
            'emission': 0.057,
            'frequency': 2
        },
        'romania_poland': {
            'from': 'N2_ROM',
            'to': 'N5_FAC',
            'mode': 'truck',
            'vehicle': 'truck',
            'capacity': 600,
            'speed': 80,
            'emission': 0.057,
            'frequency': 3
        },
        'germany_poland': {
            'from': 'N3_DE',
            'to': 'N5_FAC',
            'mode': 'truck',
            'vehicle': 'truck',
            'capacity': 600,
            'speed': 80,
            'emission': 0.057,
            'frequency': 4
        },
        'poland_germany': {
            'from': 'N5_FAC',
            'to': 'N6_DC',
            'mode': 'truck',
            'vehicle': 'truck',
            'capacity': 600,
            'speed': 80,
            'emission': 0.057,
            'frequency': 1
        },
        'germany_uk': {
            'from': 'N6_DC',
            'to': 'N7_UK',
            'mode': 'truck',
            'vehicle': 'truck',
            'capacity': 600,
            'speed': 80,
            'emission': 0.057,
            'frequency': 2
        },
        'germany_france': {
            'from': 'N6_DC',
            'to': 'N9_FR',
            'mode': 'truck',
            'vehicle': 'truck',
            'capacity': 600,
            'speed': 80,
            'emission': 0.057,
            'frequency': 2
        },
        'germany_italy': {
            'from': 'N6_DC',
            'to': 'N10_IT',
            'mode': 'truck',
            'vehicle': 'truck',
            'capacity': 600,
            'speed': 80,
            'emission': 0.057,
            'frequency': 3
        },
        'germany_usa': {
            'from': 'N6_DC',
            'to': 'N8_US',
            'mode': 'air',
            'vehicle': 'plane',
            'capacity': 2550,
            'speed': 900,
            'emission': 0.500,
            'frequency': 7
        }
    }

    # Add markers for all nodes
    for node_id, node_data in nodes.items():
        icon_color = {
            'raw_materials': 'green',
            'manufacturing': 'blue',
            'distribution': 'orange',
            'retail': 'red'
        }[node_data['type']]

        icon_type = {
            'tree': 'tree',
            'flask': 'flask',
            'cogs': 'cogs',
            'industry': 'industry',
            'warehouse': 'warehouse',
            'shopping-cart': 'shopping-cart'
        }[node_data['icon']]

        folium.Marker(
            location=node_data['coords'],
            popup=f"""
            <div style="width: 200px;">
                <h4>{node_data['name']}</h4>
                <p><strong>Product:</strong> {node_data['product']}</p>
                <p><strong>Type:</strong> {node_data['type'].title()}</p>
                <p><strong>Capacity:</strong> {node_data['capacity']} units</p>
                <div id="inventory-{node_id}">Loading...</div>
            </div>
            """,
            icon=folium.Icon(color=icon_color, icon=icon_type, prefix='fa')
        ).add_to(m)

    # Store route coordinates for JavaScript moving markers
    route_coordinates = {}

    # Calculate and add routes
    for route_id, route_data in routes.items():
        from_node = nodes[route_data['from']]
        to_node = nodes[route_data['to']]

        if route_data['mode'] == 'air':
            # For air routes, use geodesic lines
            route_coords = [from_node['coords'], to_node['coords']]
        elif 'waypoints' in route_data:
            # Use predefined waypoints for China->Poland rail
            route_coords = route_data['waypoints']
        else:
            # Use OSRM for road routes
            route_coords = get_osrm_route(from_node['coords'], to_node['coords'])
            if not route_coords or len(route_coords) < 2:
                # Fallback to straight line if OSRM fails
                print(f"OSRM failed for {route_id}, using straight line")
                route_coords = [from_node['coords'], to_node['coords']]

        # Store coordinates for JavaScript
        route_coordinates[route_id] = route_coords

        # Add AntPath for route visualization
        plugins.AntPath(
            locations=route_coords,
            color={
                'truck': 'blue',
                'rail': 'green',
                'air': 'red',
                'multimodal': 'purple'
            }.get(route_data.get('mode', 'truck'), 'blue'),
            weight=4,
            opacity=0.7,
            dash_array=[15, 30] if route_data.get('mode') == 'rail' else [10, 20],
            pulse_color='#ffffff',
            delay=1000
        ).add_to(m)

    # Create the HTML template with JavaScript
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>IKEA Supply Chain Simulation</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://unpkg.com/leaflet-moving-marker@0.0.1/dist/leaflet.moving-marker.min.js"></script>
    <!DOCTYPE html>
    <html>
    <head>
        <title>IKEA Supply Chain Simulation</title>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css" />
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                overflow: hidden;
            }}
            #map {{
                height: 100vh;
                width: 100%;
            }}
            .control-panel {{
                position: absolute;
                top: 10px;
                left: 10px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
                min-width: 250px;
            }}
            .control-panel.collapsed {{
                height: 40px;
                overflow: hidden;
            }}
            .panel-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
                cursor: pointer;
            }}
            .panel-toggle {{
                background: none;
                border: none;
                font-size: 16px;
                cursor: pointer;
            }}
            .control-buttons {{
                display: flex;
                gap: 10px;
                margin-bottom: 10px;
            }}
            .speed-slider {{
                width: 100%;
                margin-bottom: 10px;
            }}
            .scenario-selector {{
                width: 100%;
                padding: 5px;
                margin-bottom: 10px;
            }}
            .inspector-panel {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
                min-width: 300px;
                max-height: 80vh;
                overflow-y: auto;
            }}
            .inspector-panel.collapsed {{
                height: 40px;
                overflow: hidden;
            }}
            .charts-panel {{
                position: absolute;
                bottom: 10px;
                left: 10px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
                width: 600px;
                height: 300px;
            }}
            .charts-panel.collapsed {{
                height: 40px;
                overflow: hidden;
            }}
            .chart-container {{
                height: 250px;
                margin-bottom: 20px;
            }}
            .legend-panel {{
                position: absolute;
                bottom: 10px;
                right: 10px;
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 1000;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                margin-bottom: 5px;
            }}
            .legend-color {{
                width: 20px;
                height: 20px;
                margin-right: 10px;
                border-radius: 3px;
            }}
            button {{
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                background: #007cba;
                color: white;
            }}
            button:hover {{
                background: #005a87;
            }}
            button.pause {{
                background: #dc3545;
            }}
            button.pause:hover {{
                background: #c82333;
            }}
            .data-display {{
                margin-top: 10px;
            }}
            .data-row {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
            }}
            .vehicle-icon {{
                background: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }}
            .vehicle-icon div {{
                text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                line-height: 1;
            }}
        </style>
    </head>
    <body>
        <div id="map"></div>

        <!-- Control Panel -->
        <div class="control-panel" id="controlPanel">
            <div class="panel-header" onclick="togglePanel('controlPanel')">
                <h3>Simulation Controls</h3>
                <button class="panel-toggle">−</button>
            </div>
            <div class="control-buttons">
                <button id="playPauseBtn" onclick="toggleSimulation()">Play</button>
                <button onclick="resetSimulation()">Reset</button>
            </div>
            <div>
                <label>Speed: <span id="speedValue">1x</span></label>
                <input type="range" id="speedSlider" class="speed-slider" min="0.1" max="10" step="0.1" value="1">
            </div>
            <select id="scenarioSelector" class="scenario-selector">
                <option value="baseline">Baseline (Current Ops)</option>
                <option value="green_rail">Green Rail (Shift Romania Trucks to Rail)</option>
                <option value="local_source">Local Source (Cancel Sweden, source all wood in Poland)</option>
            </select>
            <div class="data-display">
                <div class="data-row">
                    <span>Current Date:</span>
                    <span id="currentDate">Jan 1, 2024</span>
                </div>
                <div class="data-row">
                    <span>Simulation Time:</span>
                    <span id="simTime">00:00:00</span>
                </div>
                <div class="data-row">
                    <span>Season Multiplier:</span>
                    <span id="seasonMultiplier">1.0x</span>
                </div>
            </div>
        </div>

        <!-- Inspector Panel -->
        <div class="inspector-panel collapsed" id="inspectorPanel">
            <div class="panel-header" onclick="togglePanel('inspectorPanel')">
                <h3>Facility Inspector</h3>
                <button class="panel-toggle">+</button>
            </div>
            <div id="inspectorContent">
                <p>Click on a facility marker to inspect</p>
            </div>
        </div>

        <!-- Charts Panel -->
        <div class="charts-panel" id="chartsPanel">
            <div class="panel-header" onclick="togglePanel('chartsPanel')">
                <h3>Analytics Dashboard</h3>
                <button class="panel-toggle">−</button>
            </div>
            <div class="chart-container">
                <canvas id="co2Chart"></canvas>
            </div>
            <div class="chart-container">
                <canvas id="scenarioChart"></canvas>
            </div>
        </div>

        <!-- Legend Panel -->
        <div class="legend-panel">
            <h4>Legend</h4>
            <div class="legend-item">
                <div class="legend-color" style="background: blue;"></div>
                <span>Truck Routes</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: green;"></div>
                <span>Rail Routes</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: red;"></div>
                <span>Air Routes</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: purple;"></div>
                <span>Multimodal Routes</span>
            </div>
        </div>

        <script>
            // Global state variables
            let isPlaying = false;
            let simulationSpeed = 1;
            let currentScenario = 'baseline';
            let startDate = new Date('2024-01-01T00:00:00');
            let currentDate = new Date(startDate);
            let simulationTime = 0; // seconds
            let animationId = null;

            // Node state tracking
            const nodeState = {json.dumps({node_id: {
                'stock': node_data['initial_stock'],
                'capacity': node_data['capacity'],
                'inbound_rate': 0,
                'outbound_rate': 0,
                'production_rate': 50 if node_data['type'] == 'manufacturing' else 0,
                'sales_rate': 20 if node_data['type'] == 'retail' else 0
            } for node_id, node_data in nodes.items()}, indent=2)};

            // Transportation vehicles in transit
            const activeVehicles = [];

            // CO2 tracking
            const co2Data = {{
                baseline: {{ truck: 0, rail: 0, air: 0 }},
                green_rail: {{ truck: 0, rail: 0, air: 0 }},
                local_source: {{ truck: 0, rail: 0, air: 0 }}
            }};

            // Scenario comparison data
            const scenarioComparison = {{
                baseline: [],
                green_rail: [],
                local_source: []
            }};

            // Routes data
            const routesData = {json.dumps(routes, indent=2)};
            const nodesData = {json.dumps(nodes, indent=2)};

            // Chart instances
            let co2Chart;
            let scenarioChart;

            // Initialize charts
            function initCharts() {{
                const co2Ctx = document.getElementById('co2Chart').getContext('2d');
                co2Chart = new Chart(co2Ctx, {{
                    type: 'bar',
                    data: {{
                        labels: ['Truck', 'Rail', 'Air'],
                        datasets: [{{
                            label: 'CO2 Emissions (kg)',
                            data: [0, 0, 0],
                            backgroundColor: ['blue', 'green', 'red']
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            y: {{
                                beginAtZero: true
                            }}
                        }}
                    }}
                }});

                const scenarioCtx = document.getElementById('scenarioChart').getContext('2d');
                scenarioChart = new Chart(scenarioCtx, {{
                    type: 'line',
                    data: {{
                        labels: [],
                        datasets: [
                            {{
                                label: 'Baseline',
                                data: [],
                                borderColor: 'blue',
                                fill: false
                            }},
                            {{
                                label: 'Green Rail',
                                data: [],
                                borderColor: 'green',
                                fill: false
                            }},
                            {{
                                label: 'Local Source',
                                data: [],
                                borderColor: 'orange',
                                fill: false
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            x: {{
                                display: true,
                                title: {{
                                    display: true,
                                    text: 'Time (Days)'
                                }}
                            }},
                            y: {{
                                display: true,
                                title: {{
                                    display: true,
                                    text: 'Cumulative CO2 (kg)'
                                }}
                            }}
                        }}
                    }}
                }});
            }}

            // Toggle panel visibility
            function togglePanel(panelId) {{
                const panel = document.getElementById(panelId);
                const toggleBtn = panel.querySelector('.panel-toggle');

                if (panel.classList.contains('collapsed')) {{
                    panel.classList.remove('collapsed');
                    toggleBtn.textContent = '−';
                }} else {{
                    panel.classList.add('collapsed');
                    toggleBtn.textContent = '+';
                }}
            }}

            // Toggle simulation play/pause
            function toggleSimulation() {{
                isPlaying = !isPlaying;
                const btn = document.getElementById('playPauseBtn');

                if (isPlaying) {{
                    btn.textContent = 'Pause';
                    btn.classList.add('pause');
                    startSimulation();
                }} else {{
                    btn.textContent = 'Play';
                    btn.classList.remove('pause');
                    stopSimulation();
                }}
            }}

            // Reset simulation
            function resetSimulation() {{
                stopSimulation();
                currentDate = new Date(startDate);
                simulationTime = 0;
                isPlaying = false;

                // Reset node states
                Object.keys(nodeState).forEach(nodeId => {{
                    nodeState[nodeId].stock = nodesData[nodeId].initial_stock;
                    nodeState[nodeId].inbound_rate = 0;
                    nodeState[nodeId].outbound_rate = 0;
                }});

                // Reset CO2 data
                Object.keys(co2Data).forEach(scenario => {{
                    co2Data[scenario] = {{ truck: 0, rail: 0, air: 0 }};
                }});

                scenarioComparison.baseline = [];
                scenarioComparison.green_rail = [];
                scenarioComparison.local_source = [];

                updateDisplay();
                updateCharts();
            }}

            // Update speed
            document.getElementById('speedSlider').addEventListener('input', function(e) {{
                simulationSpeed = parseFloat(e.target.value);
                document.getElementById('speedValue').textContent = simulationSpeed.toFixed(1) + 'x';
            }});

            // Update scenario
            document.getElementById('scenarioSelector').addEventListener('change', function(e) {{
                currentScenario = e.target.value;
            }});

            // Calculate distance between two coordinates (Haversine formula)
            function calculateDistance(lat1, lon1, lat2, lon2) {{
                const R = 6371; // Earth's radius in km
                const dLat = (lat2 - lat1) * Math.PI / 180;
                const dLon = (lon2 - lon1) * Math.PI / 180;
                const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                         Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                         Math.sin(dLon/2) * Math.sin(dLon/2);
                const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(Math.sqrt(1-a)));
                return R * c;
            }}

            // Get seasonality multiplier
            function getSeasonalityMultiplier(date) {{
                const month = date.getMonth() + 1; // 1-12

                if (month === 8 || month === 9) return 1.8; // Back-to-school rush
                if (month === 1) return 1.3; // New Year
                if (month === 6 || month === 7) return 0.8; // Summer slump
                return 1.0; // Normal
            }}

            // Update node states based on scenario
            function updateNodeStates() {{
                const multiplier = getSeasonalityMultiplier(currentDate);

                Object.keys(nodeState).forEach(nodeId => {{
                    const node = nodeState[nodeId];

                    // Apply production rates (for manufacturing nodes)
                    if (nodesData[nodeId].type === 'manufacturing') {{
                        node.production_rate = 50 * multiplier;
                        node.stock = Math.min(node.capacity, node.stock + node.production_rate / 3600); // per second
                    }}

                    // Apply sales rates (for retail nodes)
                    if (nodesData[nodeId].type === 'retail') {{
                        node.sales_rate = 20 * multiplier;
                        node.stock = Math.max(0, node.stock - node.sales_rate / 3600);
                    }}

                    // Update rates based on current scenario
                    updateScenarioRates(nodeId);
                }});
            }}

            // Update rates based on current scenario
            function updateScenarioRates(nodeId) {{
                // Reset rates
                nodeState[nodeId].inbound_rate = 0;
                nodeState[nodeId].outbound_rate = 0;

                // Apply scenario-specific changes
                if (currentScenario === 'green_rail') {{
                    // Shift Romania trucks to rail
                    if (nodeId === 'N2_ROM') {{
                        // Reduce outbound to Poland
                    }}
                }} else if (currentScenario === 'local_source') {{
                    // Cancel Sweden, source all wood in Poland
                    if (nodeId === 'N1_SWE') {{
                        nodeState[nodeId].production_rate = 0;
                    }}
                    if (nodeId === 'N5_FAC') {{
                        // Increase local sourcing
                        nodeState[nodeId].production_rate *= 1.5;
                    }}
                }}
            }}

            // Update display elements
            function updateDisplay() {{
                document.getElementById('currentDate').textContent =
                    currentDate.toLocaleDateString('en-US', {{
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                    }});

                const hours = Math.floor(simulationTime / 3600);
                const minutes = Math.floor((simulationTime % 3600) / 60);
                const seconds = Math.floor(simulationTime % 60);
                document.getElementById('simTime').textContent =
                    `${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;

                document.getElementById('seasonMultiplier').textContent =
                    getSeasonalityMultiplier(currentDate).toFixed(1) + 'x';

                // Update inventory displays
                Object.keys(nodeState).forEach(nodeId => {{
                    const element = document.getElementById(`inventory-${{nodeId}}`);
                    if (element) {{
                        element.innerHTML = `<strong>Stock:</strong> ${{Math.round(nodeState[nodeId].stock)}}/${{nodeState[nodeId].capacity}} units`;
                    }}
                }});
            }}

            // Update charts
            function updateCharts() {{
                // Update CO2 bar chart
                co2Chart.data.datasets[0].data = [
                    co2Data[currentScenario].truck,
                    co2Data[currentScenario].rail,
                    co2Data[currentScenario].air
                ];
                co2Chart.update();

                // Update scenario comparison chart
                const timeLabel = Math.round(simulationTime / 86400); // days
                if (!scenarioComparison.baseline.includes(timeLabel) ||
                    scenarioComparison.baseline.length === 0) {{

                    scenarioComparison.baseline.push(timeLabel);
                    scenarioComparison.green_rail.push(timeLabel);
                    scenarioComparison.local_source.push(timeLabel);

                    // Add cumulative CO2 values
                    scenarioChart.data.labels.push(timeLabel);
                    scenarioChart.data.datasets[0].data.push(
                        co2Data.baseline.truck + co2Data.baseline.rail + co2Data.baseline.air
                    );
                    scenarioChart.data.datasets[1].data.push(
                        co2Data.green_rail.truck + co2Data.green_rail.rail + co2Data.green_rail.air
                    );
                    scenarioChart.data.datasets[2].data.push(
                        co2Data.local_source.truck + co2Data.local_source.rail + co2Data.local_source.air
                    );
                    scenarioChart.update();
                }}
            }}

            // Simulation loop with error handling
            function simulationStep() {{
                try {{
                    if (!isPlaying) return;

                    // Check for valid map reference
                    if (!theMap) {{
                        console.error('CRITICAL: Map not available during simulation step');
                        return;
                    }}

                    // Advance time
                    const deltaTime = (1/60) * simulationSpeed; // 60 FPS
                    simulationTime += deltaTime;
                    currentDate = new Date(startDate.getTime() + simulationTime * 1000);

                    // Update node states
                    updateNodeStates();

                    // Process active shipments
                    processShipments();

                    // Update display
                    updateDisplay();

                    // Update charts periodically
                    if (Math.floor(simulationTime) % 60 === 0) {{ // Every minute
                        updateCharts();
                    }}

                    // Update moving markers
                    ikeaSimulation.updateMovingMarkers();

                    animationId = requestAnimationFrame(simulationStep);
                }} catch (error) {{
                    console.error('CRITICAL: Error in simulation step:', error.message || error);
                    stopSimulation();
                }}
            }}

            // Process shipments and CO2 emissions
            function processShipments() {{
                // Simulate shipments based on inventory levels and routes
                Object.keys(routesData).forEach(routeId => {{
                    const route = routesData[routeId];
                    const fromNode = route.from;
                    const toNode = route.to;

                    // Check if we should send a shipment
                    if (nodeState[fromNode].stock > route.capacity * 0.8) {{ // 80% capacity trigger
                        const shipmentSize = Math.min(route.capacity, nodeState[fromNode].stock);
                        const distance = calculateDistance(
                            nodesData[fromNode].coords[0], nodesData[fromNode].coords[1],
                            nodesData[toNode].coords[0], nodesData[toNode].coords[1]
                        );

                        // Calculate CO2 emissions
                        const emissions = shipmentSize * distance * route.emission;

                        // Add to CO2 tracking
                        co2Data[currentScenario][route.vehicle] += emissions;

                        // Update inventory
                        nodeState[fromNode].stock -= shipmentSize;
                        nodeState[fromNode].outbound_rate += shipmentSize;

                        // Schedule arrival
                        setTimeout(() => {{
                            nodeState[toNode].stock = Math.min(
                                nodeState[toNode].capacity,
                                nodeState[toNode].stock + shipmentSize
                            );
                            nodeState[toNode].inbound_rate += shipmentSize;
                        }}, (distance / route.speed) * 3600000); // Convert to milliseconds
                    }}
                }});
            }}

            // Start simulation
            function startSimulation() {{
                if (!animationId) {{
                    simulationStep();
                }}
            }}

            // Stop simulation
            function stopSimulation() {{
                if (animationId) {{
                    cancelAnimationFrame(animationId);
                    animationId = null;
                }}
            }}

            // Initialize
            document.addEventListener('DOMContentLoaded', function() {{
                initCharts();
                updateDisplay();
            }});

            // Handle marker clicks for inspector panel
            // This would be integrated with the Folium markers
            function inspectFacility(nodeId) {{
                const node = nodesData[nodeId];
                const state = nodeState[nodeId];

                document.getElementById('inspectorContent').innerHTML = `
                    <h4>${{node.name}}</h4>
                    <div class="data-row">
                        <span>Product:</span>
                        <span>${{node.product}}</span>
                    </div>
                    <div class="data-row">
                        <span>Current Stock:</span>
                        <span>${{Math.round(state.stock)}} units</span>
                    </div>
                    <div class="data-row">
                        <span>Capacity:</span>
                        <span>${{state.capacity}} units</span>
                    </div>
                    <div class="data-row">
                        <span>Stock Level:</span>
                        <span>${{((state.stock / state.capacity) * 100).toFixed(1)}}%</span>
                    </div>
                    <div class="data-row">
                        <span>Inbound Rate:</span>
                        <span>${{Math.round(state.inbound_rate)}} units/hour</span>
                    </div>
                    <div class="data-row">
                        <span>Outbound Rate:</span>
                        <span>${{Math.round(state.outbound_rate)}} units/hour</span>
                    </div>
                    <div class="data-row">
                        <span>Production Rate:</span>
                        <span>${{Math.round(state.production_rate)}} units/hour</span>
                    </div>
                    <div class="data-row">
                        <span>Sales Rate:</span>
                        <span>${{Math.round(state.sales_rate)}} units/hour</span>
                    </div>
                `;

                document.getElementById('inspectorPanel').classList.remove('collapsed');
                document.querySelector('#inspectorPanel .panel-toggle').textContent = '−';
            }}

            // Make functions globally available
            window.togglePanel = togglePanel;
            window.toggleSimulation = toggleSimulation;
            window.resetSimulation = resetSimulation;
            window.inspectFacility = inspectFacility;
        </script>
    </body>
    </html>
    """

    # Add Chart.js CDN
    chart_js = '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
    m.get_root().html.add_child(folium.Element(chart_js))

    # Add Leaflet.MovingMarker CDN
    moving_marker_js = '<script src="https://cdn.jsdelivr.net/npm/leaflet-moving-marker@0.0.1/dist/leaflet.moving-marker.min.js"></script>'
    m.get_root().html.add_child(folium.Element(moving_marker_js))

    # Create a custom JavaScript plugin for the simulation logic
    simulation_js = """
    // IKEA Supply Chain Simulation JavaScript

    // RELIABLE MAP REFERENCE
    const mapId = 'MAP_ID_PLACEHOLDER';
    let theMap = window[mapId];
    if (!theMap) {
        console.warn("Map not immediately available, will check later. Map ID:", mapId);
    }

    var ikeaSimulation = {
        isPlaying: false,
        simulationSpeed: 1,
        currentScenario: 'baseline',
        startDate: new Date('2024-01-01T00:00:00'),
        currentDate: new Date('2024-01-01T00:00:00'),
        simulationTime: 0,
        nodeState: {json.dumps({node_id: {
            'stock': node_data['initial_stock'],
            'capacity': node_data['capacity'],
            'inbound_rate': 0,
            'outbound_rate': 0,
            'production_rate': 50 if node_data['type'] == 'manufacturing' else 0,
            'sales_rate': 20 if node_data['type'] == 'retail' else 0
        } for node_id, node_data in nodes.items()})},
        routesData: {json.dumps(routes)},
        nodesData: {json.dumps(nodes)},
        routeCoordinates: {json.dumps(route_coordinates)},
        movingMarkers: {},
        co2Data: {
            baseline: { truck: 0, rail: 0, air: 0 },
            green_rail: { truck: 0, rail: 0, air: 0 },
            local_source: { truck: 0, rail: 0, air: 0 }
        },
        scenarioComparison: {
            baseline: [],
            green_rail: [],
            local_source: []
        },
        charts: {},

        init: function() {{
            console.log('IKEA Simulation init starting...');
            // Moving markers functionality

            this.createMovingMarker = function(routeId, vehicleType) {{
                console.log('Creating moving marker for route:', routeId, 'type:', vehicleType);
                const routeCoords = this.routeCoordinates[routeId];
                console.log('Route coordinates:', routeCoords);

                if (!routeCoords || routeCoords.length < 2) {{
                    console.log('Invalid route coordinates for', routeId);
                    return null;
                }}

                const route = this.routesData[routeId];
                const speedKmh = route.speed;
                const distance = this.calculateRouteDistance(routeCoords);
                const duration = (distance / speedKmh) * 3600000 / this.simulationSpeed;

                console.log('Route distance:', distance, 'km, duration:', duration, 'ms');

                const iconHtml = this.getVehicleIcon(vehicleType);
                console.log('Vehicle icon HTML:', iconHtml);

            try {{
                // Create a simple moving marker using standard Leaflet
                const marker = L.marker(routeCoords[0], {{
                    icon: L.divIcon({{
                        html: iconHtml,
                        className: 'vehicle-icon',
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    }})
                }}).addTo(this.map);

                console.log('Moving marker created successfully for', routeId);

                this.movingMarkers[routeId] = {{
                    marker: marker,
                    routeId: routeId,
                    vehicleType: vehicleType,
                    routeCoords: routeCoords,
                    duration: duration,
                    distance: distance,
                    isMoving: false,
                    lastStartTime: 0,
                    currentPosition: 0, // index in routeCoords
                    animationId: null
                }};

                return marker;
                }} catch (error) {{
                    console.error('Error creating moving marker:', error.message || error);
                    return null;
                }}
            }};

            this.getVehicleIcon = function(vehicleType) {{
                const icons = {{
                    truck: '<div style="color: blue; font-size: 20px;">🚛</div>',
                    rail: '<div style="color: green; font-size: 20px;">🚂</div>',
                    air: '<div style="color: red; font-size: 20px;">✈️</div>',
                    multimodal: '<div style="color: purple; font-size: 20px;">🚛</div>'
                }};
                return icons[vehicleType] || icons.truck;
            }};

            this.calculateRouteDistance = function(coords) {{
                let totalDistance = 0;
                for (let i = 1; i < coords.length; i++) {{
                    totalDistance += this.calculateDistance(
                        coords[i-1][0], coords[i-1][1],
                        coords[i][0], coords[i][1]
                    );
                }}
                return totalDistance;
            }};

            this.startVehicleMovement = function(routeId) {{
                console.log('Starting vehicle movement for', routeId);
                const vehicle = this.movingMarkers[routeId];
                if (vehicle && !vehicle.isMoving && vehicle.routeCoords.length > 1) {{
                    vehicle.isMoving = true;
                    vehicle.lastStartTime = Date.now();
                    vehicle.currentPosition = 0;

                    // Calculate step duration based on total duration and number of steps
                    const stepDuration = vehicle.duration / (vehicle.routeCoords.length - 1);

                    const animate = () => {{
                        if (!vehicle.isMoving) return;

                        vehicle.currentPosition++;

                        if (vehicle.currentPosition >= vehicle.routeCoords.length) {{
                            // Vehicle has reached the end
                            this.onVehicleArrival(routeId);
                            return;
                        }}

                        // Move marker to next position
                        const nextCoord = vehicle.routeCoords[vehicle.currentPosition];
                        vehicle.marker.setLatLng(nextCoord);

                        // Schedule next movement
                        vehicle.animationId = setTimeout(animate, stepDuration);
                    }};

                    // Start animation
                    animate();
                }}
            }};

            this.onVehicleArrival = function(routeId) {{
                console.log('Vehicle arrived at destination for', routeId);
                const vehicle = this.movingMarkers[routeId];
                if (vehicle) {{
                    vehicle.isMoving = false;
                    setTimeout(() => {{
                        if (this.movingMarkers[routeId]) {{
                            this.resetVehiclePosition(routeId);
                        }}
                    }}, 3000);
                }}
            }};

            this.resetVehiclePosition = function(routeId) {{
                const vehicle = this.movingMarkers[routeId];
                if (vehicle) {{
                    // Clear any ongoing animation
                    if (vehicle.animationId) {{
                        clearTimeout(vehicle.animationId);
                        vehicle.animationId = null;
                    }}

                    // Reset to starting position
                    const routeCoords = this.routeCoordinates[routeId];
                    if (routeCoords && routeCoords.length > 0) {{
                        vehicle.marker.setLatLng(routeCoords[0]);
                    }}
                    vehicle.isMoving = false;
                    vehicle.currentPosition = 0;
                }}
            }};

            this.        initializeMovingMarkers = function() {{
            console.log('Initializing moving markers...');

            // Check for map availability
            if (!theMap) {{
                theMap = window[mapId]; // Try again
            }}
            if (!theMap) {{
                console.error('CRITICAL: Map not available for moving markers initialization');
                return;
            }}

            // Store map reference
            this.map = theMap;

                Object.keys(this.routesData).forEach(routeId => {{
                    const route = this.routesData[routeId];
                    this.createMovingMarker(routeId, route.vehicle);
                }});

                // Force start a test vehicle immediately
                setTimeout(() => {{
                    console.log('Starting test vehicle...');
                    this.startVehicleMovement('china_poland'); // Start China->Poland train
                }}, 2000);
            }};

            this.updateMovingMarkers = function() {{
                try {{
                    // Check for valid map reference before updating markers
                    if (!theMap) {{
                        console.error('CRITICAL: Map not available for moving markers update');
                        return;
                    }}

                    Object.keys(this.routesData).forEach(routeId => {{
                        const route = this.routesData[routeId];
                        const vehicle = this.movingMarkers[routeId];

                        if (vehicle && !vehicle.isMoving) {{
                            const startChance = (1 / route.frequency) * (this.simulationTime / 3600);
                            if (Math.random() < startChance * 0.5) {{
                                this.startVehicleMovement(routeId);
                            }}
                        }}
                    }});
                }} catch (error) {{
                    console.error('CRITICAL: Error updating moving markers:', error.message || error);
                }}
            }};

            console.log('Moving marker code loaded');
            this.setupEventListeners();
            this.initCharts();
            this.updateDisplay();
            console.log('IKEA Simulation initialized');
        }},

        setupEventListeners: function() {{
            console.log('Setting up event listeners...');
            const playBtn = document.getElementById('playPauseBtn');
            if (playBtn) {{
                console.log('Play button found, adding listener');
                playBtn.addEventListener('click', () => {{
                    console.log('Play button clicked');
                    this.toggleSimulation();
                }});
            }} else {{
                console.error('Play button NOT found');
            }}

            const resetBtn = document.getElementById('resetBtn');
            if (resetBtn) {{
                resetBtn.addEventListener('click', () => this.resetSimulation());
            }}

            const speedSlider = document.getElementById('speedSlider');
            if (speedSlider) {{
                speedSlider.addEventListener('input', (e) => {{
                    this.simulationSpeed = parseFloat(e.target.value);
                    document.getElementById('speedValue').textContent = this.simulationSpeed.toFixed(1) + 'x';
                }});
            }}

            const scenarioSelector = document.getElementById('scenarioSelector');
            if (scenarioSelector) {{
                scenarioSelector.addEventListener('change', (e) => {{
                    this.currentScenario = e.target.value;
                }});
            }}
            
            document.querySelectorAll('.panel-header').forEach(header => {{
                header.addEventListener('click', () => this.togglePanel(header.parentElement.id));
            }});
        }},

        toggleSimulation: function() {{
            this.isPlaying = !this.isPlaying;
            const btn = document.getElementById('playPauseBtn');
            if (this.isPlaying) {{
                btn.textContent = 'Pause';
                btn.classList.add('pause');
                this.startSimulation();
            }} else {{
                btn.textContent = 'Play';
                btn.classList.remove('pause');
                this.stopSimulation();
            }}
        }},

        resetSimulation: function() {{
            this.stopSimulation();
            this.currentDate = new Date(this.startDate);
            this.simulationTime = 0;
            this.isPlaying = false;

            Object.keys(this.nodeState).forEach(nodeId => {{
                this.nodeState[nodeId].stock = this.nodesData[nodeId].initial_stock;
                this.nodeState[nodeId].inbound_rate = 0;
                this.nodeState[nodeId].outbound_rate = 0;
            }});

            Object.keys(this.co2Data).forEach(scenario => {{
                this.co2Data[scenario] = {{ truck: 0, rail: 0, air: 0 }};
            }});

            this.scenarioComparison = {{
                baseline: [],
                green_rail: [],
                local_source: []
            }};

            this.updateDisplay();
            this.updateCharts();
        }},

        getSeasonalityMultiplier: function(date) {{
            const month = date.getMonth() + 1;
            if (month === 8 || month === 9) return 1.8;
            if (month === 1) return 1.3;
            if (month === 6 || month === 7) return 0.8;
            return 1.0;
        }},

        calculateDistance: function(lat1, lon1, lat2, lon2) {{
            const R = 6371;
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                     Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                     Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(Math.sqrt(1-a)));
            return R * c;
        }},

        updateNodeStates: function() {{
            const multiplier = this.getSeasonalityMultiplier(this.currentDate);

            Object.keys(this.nodeState).forEach(nodeId => {{
                const node = this.nodeState[nodeId];
                if (this.nodesData[nodeId].type === 'manufacturing') {{
                    node.production_rate = 50 * multiplier;
                    node.stock = Math.min(node.capacity, node.stock + node.production_rate / 3600);
                }}
                if (this.nodesData[nodeId].type === 'retail') {{
                    node.sales_rate = 20 * multiplier;
                    node.stock = Math.max(0, node.stock - node.sales_rate / 3600);
                }}
                this.updateScenarioRates(nodeId);
            }});
        }},

        updateScenarioRates: function(nodeId) {{
            this.nodeState[nodeId].inbound_rate = 0;
            this.nodeState[nodeId].outbound_rate = 0;

            if (this.currentScenario === 'green_rail') {{
                if (nodeId === 'N2_ROM') {{
                    // Reduce Romania outbound
                }}
            }} else if (this.currentScenario === 'local_source') {{
                if (nodeId === 'N1_SWE') {{
                    this.nodeState[nodeId].production_rate = 0;
                }}
                if (nodeId === 'N5_FAC') {{
                    this.nodeState[nodeId].production_rate *= 1.5;
                }}
            }}
        }},

        processShipments: function() {{
            Object.keys(this.routesData).forEach(routeId => {{
                const route = this.routesData[routeId];
                const fromNode = route.from;
                const toNode = route.to;

                if (this.nodeState[fromNode].stock > route.capacity * 0.8) {{
                    const shipmentSize = Math.min(route.capacity, this.nodeState[fromNode].stock);
                    const distance = this.calculateDistance(
                        this.nodesData[fromNode].coords[0], this.nodesData[fromNode].coords[1],
                        this.nodesData[toNode].coords[0], this.nodesData[toNode].coords[1]
                    );

                    const emissions = shipmentSize * distance * route.emission;
                    this.co2Data[this.currentScenario][route.vehicle] += emissions;

                    this.nodeState[fromNode].stock -= shipmentSize;
                    this.nodeState[fromNode].outbound_rate += shipmentSize;

                    setTimeout(() => {{
                        this.nodeState[toNode].stock = Math.min(
                            this.nodeState[toNode].capacity,
                            this.nodeState[toNode].stock + shipmentSize
                        );
                        this.nodeState[toNode].inbound_rate += shipmentSize;
                    }}, (distance / route.speed) * 3600000);
                }}
            }});
        }},

        updateDisplay: function() {{
            document.getElementById('currentDate').textContent =
                this.currentDate.toLocaleDateString('en-US', {{
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                }});

            const hours = Math.floor(this.simulationTime / 3600);
            const minutes = Math.floor((this.simulationTime % 3600) / 60);
            const seconds = Math.floor(this.simulationTime % 60);
            document.getElementById('simTime').textContent =
                `${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;

            document.getElementById('seasonMultiplier').textContent =
                this.getSeasonalityMultiplier(this.currentDate).toFixed(1) + 'x';

            Object.keys(this.nodeState).forEach(nodeId => {{
                const element = document.getElementById(`inventory-${{nodeId}}`);
                if (element) {{
                    const stock = Math.round(this.nodeState[nodeId].stock);
                    const capacity = this.nodeState[nodeId].capacity;
                    element.innerHTML = `<strong>Stock:</strong> ${{stock}}/${{capacity}} units`;
                }}
            }});
        }},

        initCharts: function() {{
            const co2Ctx = document.getElementById('co2Chart').getContext('2d');
            this.charts.co2Chart = new Chart(co2Ctx, {{
                type: 'bar',
                data: {{
                    labels: ['Truck', 'Rail', 'Air'],
                    datasets: [{{
                        label: 'CO2 Emissions (kg)',
                        data: [0, 0, 0],
                        backgroundColor: ['blue', 'green', 'red']
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        y: {{ beginAtZero: true }}
                    }}
                }}
            }});

            const scenarioCtx = document.getElementById('scenarioChart').getContext('2d');
            this.charts.scenarioChart = new Chart(scenarioCtx, {{
                type: 'line',
                data: {{
                    labels: [],
                    datasets: [
                        {{
                            label: 'Baseline',
                            data: [],
                            borderColor: 'blue',
                            fill: false
                        }},
                        {{
                            label: 'Green Rail',
                            data: [],
                            borderColor: 'green',
                            fill: false
                        }},
                        {{
                            label: 'Local Source',
                            data: [],
                            borderColor: 'orange',
                            fill: false
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: 'Time (Days)'
                            }}
                        }},
                        y: {{
                            title: {{
                                display: true,
                                text: 'Cumulative CO2 (kg)'
                            }}
                        }}
                    }}
                }}
            }});
        }},

        updateCharts: function() {{
            this.charts.co2Chart.data.datasets[0].data = [
                this.co2Data[this.currentScenario].truck,
                this.co2Data[this.currentScenario].rail,
                this.co2Data[this.currentScenario].air
            ];
            this.charts.co2Chart.update();

            const timeLabel = Math.round(this.simulationTime / 86400);
            if (!this.scenarioComparison.baseline.includes(timeLabel)) {{
                ['baseline', 'green_rail', 'local_source'].forEach(scenario => {{
                    this.scenarioComparison[scenario].push(timeLabel);
                }});

                this.charts.scenarioChart.data.labels.push(timeLabel);
                this.charts.scenarioChart.data.datasets[0].data.push(
                    this.co2Data.baseline.truck + this.co2Data.baseline.rail + this.co2Data.baseline.air
                );
                this.charts.scenarioChart.data.datasets[1].data.push(
                    this.co2Data.green_rail.truck + this.co2Data.green_rail.rail + this.co2Data.green_rail.air
                );
                this.charts.scenarioChart.data.datasets[2].data.push(
                    this.co2Data.local_source.truck + this.co2Data.local_source.rail + this.co2Data.local_source.air
                );
                this.charts.scenarioChart.update();
            }}
        }},

        simulationStep: function() {{
            try {{
                if (!this.isPlaying) return;

                // Check for valid map reference
                if (!theMap) {{
                    theMap = window[mapId]; // Try to get map again
                }}
                if (!theMap) {{
                    console.warn('Map not available during simulation step, skipping update');
                    return;
                }}

                const deltaTime = (1/60) * this.simulationSpeed;
                this.simulationTime += deltaTime;
                this.currentDate = new Date(this.startDate.getTime() + this.simulationTime * 1000);

                this.updateNodeStates();
                this.processShipments();
                this.updateDisplay();

                if (Math.floor(this.simulationTime) % 60 === 0) {{
                    this.updateCharts();
                }}

                requestAnimationFrame(() => this.simulationStep());
            }} catch (error) {{
                console.error('CRITICAL: Error in simulation step:', error.message || error);
                this.isPlaying = false;
            }}
        }},

        startSimulation: function() {{
            this.simulationStep();
        }},

        stopSimulation: function() {{
            // Animation will stop automatically when isPlaying becomes false
        }},

        inspectFacility: function(nodeId) {{
            const node = this.nodesData[nodeId];
            const state = this.nodeState[nodeId];

            document.getElementById('inspectorContent').innerHTML = `
                <h4>${{node.name}}</h4>
                <div class="data-row">
                    <span>Product:</span>
                    <span>${{node.product}}</span>
                </div>
                <div class="data-row">
                    <span>Current Stock:</span>
                    <span>${{Math.round(state.stock)}} units</span>
                </div>
                <div class="data-row">
                    <span>Capacity:</span>
                    <span>${{state.capacity}} units</span>
                </div>
                <div class="data-row">
                    <span>Stock Level:</span>
                    <span>${{((state.stock / state.capacity) * 100).toFixed(1)}}%</span>
                </div>
                <div class="data-row">
                    <span>Inbound Rate:</span>
                    <span>${{Math.round(state.inbound_rate)}} units/hour</span>
                </div>
                <div class="data-row">
                    <span>Outbound Rate:</span>
                    <span>${{Math.round(state.outbound_rate)}} units/hour</span>
                </div>
                <div class="data-row">
                    <span>Production Rate:</span>
                    <span>${{Math.round(state.production_rate)}} units/hour</span>
                </div>
                <div class="data-row">
                    <span>Sales Rate:</span>
                    <span>${{Math.round(state.sales_rate)}} units/hour</span>
                </div>
            `;

            document.getElementById('inspectorPanel').classList.remove('collapsed');
            document.querySelector('#inspectorPanel .panel-toggle').textContent = '−';
        }}
    }};
    """

    # Format the simulation_js with the captured map_id
    simulation_js = simulation_js.replace('MAP_ID_PLACEHOLDER', map_id)

    # Add moving marker functions to the main simulation script
    moving_marker_code = """
        // Moving markers functionality
        this.movingMarkers = {};

        this.createMovingMarker = function(routeId, vehicleType) {
            console.log('Creating moving marker for route:', routeId, 'type:', vehicleType);
            const routeCoords = this.routeCoordinates[routeId];
            console.log('Route coordinates:', routeCoords);

            if (!routeCoords || routeCoords.length < 2) {
                console.log('Invalid route coordinates for', routeId);
                return null;
            }

            const route = this.routesData[routeId];
            const speedKmh = route.speed;
            const distance = this.calculateRouteDistance(routeCoords);
            const duration = (distance / speedKmh) * 3600000 / this.simulationSpeed;

            console.log('Route distance:', distance, 'km, duration:', duration, 'ms');

            const iconHtml = this.getVehicleIcon(vehicleType);
            console.log('Vehicle icon HTML:', iconHtml);

            try {
                const marker = L.Marker.movingMarker(routeCoords, [duration], {
                    icon: L.divIcon({
                        html: iconHtml,
                        className: 'vehicle-icon',
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    }),
                    autostart: false
                }).addTo(map);

                console.log('Moving marker created successfully for', routeId);

                this.movingMarkers[routeId] = {
                    marker: marker,
                    routeId: routeId,
                    vehicleType: vehicleType,
                    duration: duration,
                    distance: distance,
                    isMoving: false,
                    lastStartTime: 0
                };

                return marker;
            } catch (error) {
                console.error('Error creating moving marker:', error);
                return null;
            }
        };

        this.getVehicleIcon = function(vehicleType) {
            const icons = {
                truck: '<div style="color: blue; font-size: 20px;">🚛</div>',
                rail: '<div style="color: green; font-size: 20px;">🚂</div>',
                air: '<div style="color: red; font-size: 20px;">✈️</div>',
                multimodal: '<div style="color: purple; font-size: 20px;">🚛</div>'
            };
            return icons[vehicleType] || icons.truck;
        };

        this.calculateRouteDistance = function(coords) {
            let totalDistance = 0;
            for (let i = 1; i < coords.length; i++) {
                totalDistance += this.calculateDistance(
                    coords[i-1][0], coords[i-1][1],
                    coords[i][0], coords[i][1]
                );
            }
            return totalDistance;
        };

        this.startVehicleMovement = function(routeId) {
            console.log('Starting vehicle movement for', routeId);
            const vehicle = this.movingMarkers[routeId];
            if (vehicle && !vehicle.isMoving) {
                vehicle.marker.start();
                vehicle.isMoving = true;
                vehicle.lastStartTime = Date.now();

                setTimeout(() => {
                    this.onVehicleArrival(routeId);
                }, vehicle.duration);
            }
        };

        this.onVehicleArrival = function(routeId) {
            console.log('Vehicle arrived at destination for', routeId);
            const vehicle = this.movingMarkers[routeId];
            if (vehicle) {
                vehicle.isMoving = false;
                setTimeout(() => {
                    if (this.movingMarkers[routeId]) {
                        this.resetVehiclePosition(routeId);
                    }
                }, 3000);
            }
        };

        this.resetVehiclePosition = function(routeId) {
            const vehicle = this.movingMarkers[routeId];
            if (vehicle) {
                vehicle.marker.stop();
                const routeCoords = this.routeCoordinates[routeId];
                if (routeCoords && routeCoords.length > 0) {
                    vehicle.marker.setLatLng(routeCoords[0]);
                }
                vehicle.isMoving = false;
            }
        };

        this.initializeMovingMarkers = function() {
            console.log('Initializing moving markers...');
            Object.keys(this.routesData).forEach(routeId => {
                const route = this.routesData[routeId];
                this.createMovingMarker(routeId, route.vehicle);
            });

            // Force start a test vehicle immediately
            setTimeout(() => {
                console.log('Starting test vehicle...');
                this.startVehicleMovement('china_poland'); // Start China->Poland train
            }, 2000);
        };

        this.updateMovingMarkers = function() {
            try {
                // Check for valid map reference before updating markers
                if (!theMap) {
                    console.error('CRITICAL: Map not available for moving markers update');
                    return;
                }

                Object.keys(this.routesData).forEach(routeId => {
                    const route = this.routesData[routeId];
                    const vehicle = this.movingMarkers[routeId];

                    if (vehicle && !vehicle.isMoving) {
                        const startChance = (1 / route.frequency) * (this.simulationTime / 3600);
                        if (Math.random() < startChance * 0.5) {
                            this.startVehicleMovement(routeId);
                        }
                    }
                });
            } catch (error) {
                console.error('CRITICAL: Error updating moving markers:', error.message || error);
            }
        };
    """

    # Insert the moving marker code into the init function
    init_content = f"""
            {moving_marker_code}
            """

    simulation_js = simulation_js.replace(
        "        init: function() {\n            this.setupEventListeners();\n            this.initCharts();\n            this.updateDisplay();\n            console.log('IKEA Simulation initialized');\n        },",
        f"        init: function() {{\n            {init_content}\n            this.setupEventListeners();\n            this.initCharts();\n            this.updateDisplay();\n            console.log('IKEA Simulation initialized');\n        }},"
    )

    # Fix double braces for JavaScript syntax
    simulation_js = simulation_js.replace('{{', '{')
    simulation_js = simulation_js.replace('}}', '}')

    # Use minimal data for now to get basic structure working
    simulation_js = simulation_js.replace(
        "{json.dumps({node_id: {\n            'stock': node_data['initial_stock'],\n            'capacity': node_data['capacity'],\n            'inbound_rate': 0,\n            'outbound_rate': 0,\n            'production_rate': 50 if node_data['type'] == 'manufacturing' else 0,\n            'sales_rate': 20 if node_data['type'] == 'retail' else 0\n        } for node_id, node_data in nodes.items()})}",
        "{}"
    )

    simulation_js = simulation_js.replace(
        "{json.dumps(routes)}",
        "{}"
    )

    simulation_js = simulation_js.replace(
        "{json.dumps(nodes)}",
        "{}"
    )

    simulation_js = simulation_js.replace(
        "{json.dumps(route_coordinates)}",
        "{}"
    )

    # Write JavaScript to a separate file and include it
    with open('ikea_simulation.js', 'w') as f:
        f.write(simulation_js)

    # Add custom CSS
    custom_css = """
    <style>
    .control-panel {
        position: absolute;
        top: 10px;
        left: 10px;
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
        min-width: 250px;
    }
    .control-panel.collapsed {
        height: 40px;
        overflow: hidden;
    }
    .panel-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        cursor: pointer;
    }
    .panel-toggle {
        background: none;
        border: none;
        font-size: 16px;
        cursor: pointer;
    }
    .control-buttons {
        display: flex;
        gap: 10px;
        margin-bottom: 10px;
    }
    .speed-slider {
        width: 100%;
        margin-bottom: 10px;
    }
    .scenario-selector {
        width: 100%;
        padding: 5px;
        margin-bottom: 10px;
    }
    .inspector-panel {
        position: absolute;
        top: 10px;
        right: 10px;
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
        min-width: 300px;
        max-height: 80vh;
        overflow-y: auto;
    }
    .inspector-panel.collapsed {
        height: 40px;
        overflow: hidden;
    }
    .charts-panel {
        position: absolute;
        bottom: 10px;
        left: 10px;
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
        width: 600px;
        height: 300px;
    }
    .charts-panel.collapsed {
        height: 40px;
        overflow: hidden;
    }
    .chart-container {
        height: 250px;
        margin-bottom: 20px;
    }
    .legend-panel {
        position: absolute;
        bottom: 10px;
        right: 10px;
        background: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        z-index: 1000;
    }
    .legend-item {
        display: flex;
        align-items: center;
        margin-bottom: 5px;
    }
    .legend-color {
        width: 20px;
        height: 20px;
        margin-right: 10px;
        border-radius: 3px;
    }
    button {
        padding: 8px 12px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        background: #007cba;
        color: white;
    }
    button:hover {
        background: #005a87;
    }
    button.pause {
        background: #dc3545;
    }
    button.pause:hover {
        background: #c82333;
    }
    .data-display {
        margin-top: 10px;
    }
    .data-row {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
    }
    .vehicle-icon {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    .vehicle-icon div {
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        line-height: 1;
    }
    </style>
    """

    # 1. Inject CSS (Header)
    m.get_root().header.add_child(folium.Element(custom_css))

    # Add HTML elements for UI panels
    ui_html = """
    <!-- Control Panel -->
    <div class="control-panel" id="controlPanel">
        <div class="panel-header" onclick="this.parentElement.classList.toggle('collapsed');
                                         this.querySelector('.panel-toggle').textContent =
                                         this.parentElement.classList.contains('collapsed') ? '+' : '−'">
            <h3>Simulation Controls</h3>
            <button class="panel-toggle">−</button>
        </div>
        <div class="control-buttons">
            <button id="playPauseBtn">Play</button>
            <button id="resetBtn">Reset</button>
        </div>
        <div>
            <label>Speed: <span id="speedValue">1x</span></label>
            <input type="range" id="speedSlider" class="speed-slider" min="0.1" max="10" step="0.1" value="1">
        </div>
        <select id="scenarioSelector" class="scenario-selector">
            <option value="baseline">Baseline (Current Ops)</option>
            <option value="green_rail">Green Rail (Shift Romania Trucks to Rail)</option>
            <option value="local_source">Local Source (Cancel Sweden, source all wood in Poland)</option>
        </select>
        <div class="data-display">
            <div class="data-row">
                <span>Current Date:</span>
                <span id="currentDate">Jan 1, 2024</span>
            </div>
            <div class="data-row">
                <span>Simulation Time:</span>
                <span id="simTime">00:00:00</span>
            </div>
            <div class="data-row">
                <span>Season Multiplier:</span>
                <span id="seasonMultiplier">1.0x</span>
            </div>
        </div>
    </div>

    <!-- Inspector Panel -->
    <div class="inspector-panel collapsed" id="inspectorPanel">
        <div class="panel-header" onclick="this.parentElement.classList.toggle('collapsed');
                                         this.querySelector('.panel-toggle').textContent =
                                         this.parentElement.classList.contains('collapsed') ? '+' : '−'">
            <h3>Facility Inspector</h3>
            <button class="panel-toggle">+</button>
        </div>
        <div id="inspectorContent">
            <p>Click on a facility marker to inspect</p>
        </div>
    </div>

    <!-- Charts Panel -->
    <div class="charts-panel" id="chartsPanel">
        <div class="panel-header" onclick="this.parentElement.classList.toggle('collapsed');
                                         this.querySelector('.panel-toggle').textContent =
                                         this.parentElement.classList.contains('collapsed') ? '+' : '−'">
            <h3>Analytics Dashboard</h3>
            <button class="panel-toggle">−</button>
        </div>
        <div class="chart-container">
            <canvas id="co2Chart"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="scenarioChart"></canvas>
        </div>
    </div>

    <!-- Legend Panel -->
    <div class="legend-panel">
        <h4>Legend</h4>
        <div class="legend-item">
            <div class="legend-color" style="background: blue;"></div>
            <span>Truck Routes</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: green;"></div>
            <span>Rail Routes</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: red;"></div>
            <span>Air Routes</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: purple;"></div>
            <span>Multimodal Routes</span>
        </div>
    </div>
    """

    # 2. Inject UI HTML (Body) - MUST BE BEFORE JS
    m.get_root().html.add_child(folium.Element(ui_html))

    # Insert the moving marker code into the init function
    init_content = f"""
            {moving_marker_code}
            """

    simulation_js = simulation_js.replace(
        "        init: function() {\\n            this.setupEventListeners();\\n            this.initCharts();\\n            this.updateDisplay();\\n            console.log('IKEA Simulation initialized');\\n        },",
        f"        init: function() {{\\n            {init_content}\\n            this.setupEventListeners();\\n            this.initCharts();\\n            this.updateDisplay();\\n            console.log('IKEA Simulation initialized');\\n        }},"
    )

    # Fix double braces for JavaScript syntax
    simulation_js = simulation_js.replace('{{', '{')
    simulation_js = simulation_js.replace('}}', '}')

    # Use minimal data for now to get basic structure working
    simulation_js = simulation_js.replace(
        "{json.dumps({node_id: {\\n            'stock': node_data['initial_stock'],\\n            'capacity': node_data['capacity'],\\n            'inbound_rate': 0,\\n            'outbound_rate': 0,\\n            'production_rate': 50 if node_data['type'] == 'manufacturing' else 0,\\n            'sales_rate': 20 if node_data['type'] == 'retail' else 0\\n        } for node_id, node_data in nodes.items()})}",
        "{}"
    )

    simulation_js = simulation_js.replace(
        "{json.dumps(routes)}",
        "{}"
    )

    simulation_js = simulation_js.replace(
        "{json.dumps(nodes)}",
        "{}"
    )

    simulation_js = simulation_js.replace(
        "{json.dumps(route_coordinates)}",
        "{}"
    )
    
    # Add safeguard to initialization
    simulation_js += """
    // Safeguard initialization
    window.addEventListener('load', function() {
        console.log('Window loaded, initializing...');
        setTimeout(() => { 
            if (typeof ikeaSimulation !== 'undefined') {
                ikeaSimulation.init(); 
            } else {
                console.error('ikeaSimulation not defined!');
            }
        }, 1000);
    });
    """

    # Write JavaScript to a separate file and include it
    with open('ikea_simulation.js', 'w') as f:
        f.write(simulation_js)

    # 3. Inject JS Libraries and Simulation Script (Body) - LAST
    # Note: Leaflet and other libs are already added by Folium or in the template
    # We just need to add our custom script
    js_include = '<script src="ikea_simulation.js"></script>'
    m.get_root().html.add_child(folium.Element(js_include))

    # Save the map
    output_file = 'ikea_master_simulation.html'
    m.save(output_file)
    print(f"IKEA Supply Chain Simulation saved as '{output_file}'")
    
    # Serve the file
    serve_simulation(output_file)

def serve_simulation(output_file):
    """Serve the simulation file via a local HTTP server"""
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    
    # Find a free port
    while True:
        try:
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"Serving at http://localhost:{PORT}")
                
                # Open browser in a separate thread to ensure server is ready
                def open_browser():
                    time.sleep(1.5) # Give server a moment to start
                    url = f"http://localhost:{PORT}/{output_file}"
                    print(f"Opening {url}...")
                    webbrowser.open(url)
                
                threading.Thread(target=open_browser).start()
                
                print("Press Ctrl+C to stop the server")
                try:
                    httpd.serve_forever()
                except KeyboardInterrupt:
                    print("\\nServer stopped.")
                    break
        except OSError:
            PORT += 1


if __name__ == "__main__":
    create_ikea_simulation()

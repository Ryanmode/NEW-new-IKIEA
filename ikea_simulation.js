
    // IKEA Supply Chain Simulation JavaScript

    // RELIABLE MAP REFERENCE
    const mapId = 'map_ff4111e2d3b9bc2c87b322b29f5807bd';
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
        nodeState: {},
        routesData: {},
        nodesData: {},
        routeCoordinates: {},
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

        init: function() {
            console.log('IKEA Simulation init starting...');
            // Moving markers functionality

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
                // Create a simple moving marker using standard Leaflet
                const marker = L.marker(routeCoords[0], {
                    icon: L.divIcon({
                        html: iconHtml,
                        className: 'vehicle-icon',
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    })
                }).addTo(this.map);

                console.log('Moving marker created successfully for', routeId);

                this.movingMarkers[routeId] = {
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
                };

                return marker;
                } catch (error) {
                    console.error('Error creating moving marker:', error.message || error);
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
                if (vehicle && !vehicle.isMoving && vehicle.routeCoords.length > 1) {
                    vehicle.isMoving = true;
                    vehicle.lastStartTime = Date.now();
                    vehicle.currentPosition = 0;

                    // Calculate step duration based on total duration and number of steps
                    const stepDuration = vehicle.duration / (vehicle.routeCoords.length - 1);

                    const animate = () => {
                        if (!vehicle.isMoving) return;

                        vehicle.currentPosition++;

                        if (vehicle.currentPosition >= vehicle.routeCoords.length) {
                            // Vehicle has reached the end
                            this.onVehicleArrival(routeId);
                            return;
                        }

                        // Move marker to next position
                        const nextCoord = vehicle.routeCoords[vehicle.currentPosition];
                        vehicle.marker.setLatLng(nextCoord);

                        // Schedule next movement
                        vehicle.animationId = setTimeout(animate, stepDuration);
                    };

                    // Start animation
                    animate();
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
                    // Clear any ongoing animation
                    if (vehicle.animationId) {
                        clearTimeout(vehicle.animationId);
                        vehicle.animationId = null;
                    }

                    // Reset to starting position
                    const routeCoords = this.routeCoordinates[routeId];
                    if (routeCoords && routeCoords.length > 0) {
                        vehicle.marker.setLatLng(routeCoords[0]);
                    }
                    vehicle.isMoving = false;
                    vehicle.currentPosition = 0;
                }
            };

            this.        initializeMovingMarkers = function() {
            console.log('Initializing moving markers...');

            // Check for map availability
            if (!theMap) {
                theMap = window[mapId]; // Try again
            }
            if (!theMap) {
                console.error('CRITICAL: Map not available for moving markers initialization');
                return;
            }

            // Store map reference
            this.map = theMap;

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

            console.log('Moving marker code loaded');
            this.setupEventListeners();
            this.initCharts();
            this.updateDisplay();
            console.log('IKEA Simulation initialized');
        },

        setupEventListeners: function() {
            document.getElementById('playPauseBtn').addEventListener('click', () => this.toggleSimulation());
            document.getElementById('resetBtn').addEventListener('click', () => this.resetSimulation());
            document.getElementById('speedSlider').addEventListener('input', (e) => {
                this.simulationSpeed = parseFloat(e.target.value);
                document.getElementById('speedValue').textContent = this.simulationSpeed.toFixed(1) + 'x';
            });
            document.getElementById('scenarioSelector').addEventListener('change', (e) => {
                this.currentScenario = e.target.value;
            });
        },

        toggleSimulation: function() {
            this.isPlaying = !this.isPlaying;
            const btn = document.getElementById('playPauseBtn');
            if (this.isPlaying) {
                btn.textContent = 'Pause';
                btn.classList.add('pause');
                this.startSimulation();
            } else {
                btn.textContent = 'Play';
                btn.classList.remove('pause');
                this.stopSimulation();
            }
        },

        resetSimulation: function() {
            this.stopSimulation();
            this.currentDate = new Date(this.startDate);
            this.simulationTime = 0;
            this.isPlaying = false;

            Object.keys(this.nodeState).forEach(nodeId => {
                this.nodeState[nodeId].stock = this.nodesData[nodeId].initial_stock;
                this.nodeState[nodeId].inbound_rate = 0;
                this.nodeState[nodeId].outbound_rate = 0;
            });

            Object.keys(this.co2Data).forEach(scenario => {
                this.co2Data[scenario] = { truck: 0, rail: 0, air: 0 };
            });

            this.scenarioComparison = {
                baseline: [],
                green_rail: [],
                local_source: []
            };

            this.updateDisplay();
            this.updateCharts();
        },

        getSeasonalityMultiplier: function(date) {
            const month = date.getMonth() + 1;
            if (month === 8 || month === 9) return 1.8;
            if (month === 1) return 1.3;
            if (month === 6 || month === 7) return 0.8;
            return 1.0;
        },

        calculateDistance: function(lat1, lon1, lat2, lon2) {
            const R = 6371;
            const dLat = (lat2 - lat1) * Math.PI / 180;
            const dLon = (lon2 - lon1) * Math.PI / 180;
            const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                     Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                     Math.sin(dLon/2) * Math.sin(dLon/2);
            const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(Math.sqrt(1-a)));
            return R * c;
        },

        updateNodeStates: function() {
            const multiplier = this.getSeasonalityMultiplier(this.currentDate);

            Object.keys(this.nodeState).forEach(nodeId => {
                const node = this.nodeState[nodeId];
                if (this.nodesData[nodeId].type === 'manufacturing') {
                    node.production_rate = 50 * multiplier;
                    node.stock = Math.min(node.capacity, node.stock + node.production_rate / 3600);
                }
                if (this.nodesData[nodeId].type === 'retail') {
                    node.sales_rate = 20 * multiplier;
                    node.stock = Math.max(0, node.stock - node.sales_rate / 3600);
                }
                this.updateScenarioRates(nodeId);
            });
        },

        updateScenarioRates: function(nodeId) {
            this.nodeState[nodeId].inbound_rate = 0;
            this.nodeState[nodeId].outbound_rate = 0;

            if (this.currentScenario === 'green_rail') {
                if (nodeId === 'N2_ROM') {
                    // Reduce Romania outbound
                }
            } else if (this.currentScenario === 'local_source') {
                if (nodeId === 'N1_SWE') {
                    this.nodeState[nodeId].production_rate = 0;
                }
                if (nodeId === 'N5_FAC') {
                    this.nodeState[nodeId].production_rate *= 1.5;
                }
            }
        },

        processShipments: function() {
            Object.keys(this.routesData).forEach(routeId => {
                const route = this.routesData[routeId];
                const fromNode = route.from;
                const toNode = route.to;

                if (this.nodeState[fromNode].stock > route.capacity * 0.8) {
                    const shipmentSize = Math.min(route.capacity, this.nodeState[fromNode].stock);
                    const distance = this.calculateDistance(
                        this.nodesData[fromNode].coords[0], this.nodesData[fromNode].coords[1],
                        this.nodesData[toNode].coords[0], this.nodesData[toNode].coords[1]
                    );

                    const emissions = shipmentSize * distance * route.emission;
                    this.co2Data[this.currentScenario][route.vehicle] += emissions;

                    this.nodeState[fromNode].stock -= shipmentSize;
                    this.nodeState[fromNode].outbound_rate += shipmentSize;

                    setTimeout(() => {
                        this.nodeState[toNode].stock = Math.min(
                            this.nodeState[toNode].capacity,
                            this.nodeState[toNode].stock + shipmentSize
                        );
                        this.nodeState[toNode].inbound_rate += shipmentSize;
                    }, (distance / route.speed) * 3600000);
                }
            });
        },

        updateDisplay: function() {
            document.getElementById('currentDate').textContent =
                this.currentDate.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric'
                });

            const hours = Math.floor(this.simulationTime / 3600);
            const minutes = Math.floor((this.simulationTime % 3600) / 60);
            const seconds = Math.floor(this.simulationTime % 60);
            document.getElementById('simTime').textContent =
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

            document.getElementById('seasonMultiplier').textContent =
                this.getSeasonalityMultiplier(this.currentDate).toFixed(1) + 'x';

            Object.keys(this.nodeState).forEach(nodeId => {
                const element = document.getElementById(`inventory-${nodeId}`);
                if (element) {
                    const stock = Math.round(this.nodeState[nodeId].stock);
                    const capacity = this.nodeState[nodeId].capacity;
                    element.innerHTML = `<strong>Stock:</strong> ${stock}/${capacity} units`;
                }
            });
        },

        initCharts: function() {
            const co2Ctx = document.getElementById('co2Chart').getContext('2d');
            this.charts.co2Chart = new Chart(co2Ctx, {
                type: 'bar',
                data: {
                    labels: ['Truck', 'Rail', 'Air'],
                    datasets: [{
                        label: 'CO2 Emissions (kg)',
                        data: [0, 0, 0],
                        backgroundColor: ['blue', 'green', 'red']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });

            const scenarioCtx = document.getElementById('scenarioChart').getContext('2d');
            this.charts.scenarioChart = new Chart(scenarioCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: 'Baseline',
                            data: [],
                            borderColor: 'blue',
                            fill: false
                        },
                        {
                            label: 'Green Rail',
                            data: [],
                            borderColor: 'green',
                            fill: false
                        },
                        {
                            label: 'Local Source',
                            data: [],
                            borderColor: 'orange',
                            fill: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Time (Days)'
                            }
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Cumulative CO2 (kg)'
                            }
                        }
                    }
                }
            });
        },

        updateCharts: function() {
            this.charts.co2Chart.data.datasets[0].data = [
                this.co2Data[this.currentScenario].truck,
                this.co2Data[this.currentScenario].rail,
                this.co2Data[this.currentScenario].air
            ];
            this.charts.co2Chart.update();

            const timeLabel = Math.round(this.simulationTime / 86400);
            if (!this.scenarioComparison.baseline.includes(timeLabel)) {
                ['baseline', 'green_rail', 'local_source'].forEach(scenario => {
                    this.scenarioComparison[scenario].push(timeLabel);
                });

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
            }
        },

        simulationStep: function() {
            try {
                if (!this.isPlaying) return;

                // Check for valid map reference
                if (!theMap) {
                    theMap = window[mapId]; // Try to get map again
                }
                if (!theMap) {
                    console.warn('Map not available during simulation step, skipping update');
                    return;
                }

                const deltaTime = (1/60) * this.simulationSpeed;
                this.simulationTime += deltaTime;
                this.currentDate = new Date(this.startDate.getTime() + this.simulationTime * 1000);

                this.updateNodeStates();
                this.processShipments();
                this.updateDisplay();

                if (Math.floor(this.simulationTime) % 60 === 0) {
                    this.updateCharts();
                }

                requestAnimationFrame(() => this.simulationStep());
            } catch (error) {
                console.error('CRITICAL: Error in simulation step:', error.message || error);
                this.isPlaying = false;
            }
        },

        startSimulation: function() {
            this.simulationStep();
        },

        stopSimulation: function() {
            // Animation will stop automatically when isPlaying becomes false
        },

        inspectFacility: function(nodeId) {
            const node = this.nodesData[nodeId];
            const state = this.nodeState[nodeId];

            document.getElementById('inspectorContent').innerHTML = `
                <h4>${node.name}</h4>
                <div class="data-row">
                    <span>Product:</span>
                    <span>${node.product}</span>
                </div>
                <div class="data-row">
                    <span>Current Stock:</span>
                    <span>${Math.round(state.stock)} units</span>
                </div>
                <div class="data-row">
                    <span>Capacity:</span>
                    <span>${state.capacity} units</span>
                </div>
                <div class="data-row">
                    <span>Stock Level:</span>
                    <span>${((state.stock / state.capacity) * 100).toFixed(1)}%</span>
                </div>
                <div class="data-row">
                    <span>Inbound Rate:</span>
                    <span>${Math.round(state.inbound_rate)} units/hour</span>
                </div>
                <div class="data-row">
                    <span>Outbound Rate:</span>
                    <span>${Math.round(state.outbound_rate)} units/hour</span>
                </div>
                <div class="data-row">
                    <span>Production Rate:</span>
                    <span>${Math.round(state.production_rate)} units/hour</span>
                </div>
                <div class="data-row">
                    <span>Sales Rate:</span>
                    <span>${Math.round(state.sales_rate)} units/hour</span>
                </div>
            `;

            document.getElementById('inspectorPanel').classList.remove('collapsed');
            document.querySelector('#inspectorPanel .panel-toggle').textContent = '−';
        }
    };

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        console.log('DOM ready, initializing simulation...');
        ikeaSimulation.init();
        // Initialize moving markers after a short delay to ensure map is ready
        setTimeout(() => {
            console.log('Initializing moving markers...');
            ikeaSimulation.initializeMovingMarkers();
        }, 1000);
    });
    
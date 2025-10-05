# JunctionX Uber Challenge - DriverFare

A sophisticated ride-sharing driver optimization platform that uses **Dynamic Programming** and **Machine Learning** to help drivers maximize their earnings by recommending optimal working hours and zones based on historical data, real-time conditions, and driver preferences.

## 🚀 Quick Start

### Starting the Application

#### Backend Server
```bash
cd server
docker compose build server --no-cache
docker compose up server
```
The server will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

#### Client Application
```bash
cd client
npm install
bun x expo start
```

**Important**: If you're running the client on a **physical device or iOS/Android simulator**, update the server IP address in `client/config/Config.ts` to your machine's local IP (run `ipconfig getifaddr en0` on Mac to get it).

---

## 📊 How It Works

### 1. Data Processing & Clustering

#### DBSCAN Clustering
The system uses **DBSCAN (Density-Based Spatial Clustering of Applications with Noise)** to create geographic zones:
- **Input**: Historical ride pickup and dropoff coordinates
- **Parameters**:
  - `eps = 250m` (maximum distance between points in a cluster)
  - `min_samples = 10` (minimum points to form a cluster)
- **Output**: City-specific clusters representing high-demand zones

Each cluster becomes a **node** in our mobility graph, with averaged latitude/longitude coordinates for map visualization.

### 2. Building the Mobility Graph

For each city, we construct a **directed graph** where:
- **Nodes** = Clusters (geographic zones created by DBSCAN)
- **Edges** = Possible trips between zones, containing:
  - Average fare amount
  - Average trip duration (minutes)
  - Trip counts per hour (0-23)
  - Hourly statistics (fares, times, demand)

This creates a **city-hour mobility graph** that captures how demand, pricing, and travel patterns change throughout the day.

### 3. Earning Rate Calculation

For any given cluster and hour, the system computes the **expected earning rate (€/hour)** using:

```
earning_rate = (expected_fare × surge_multiplier × weather_multiplier) / total_time
```

Where:
- **Expected Fare** = Weighted average of fares to all reachable zones based on transition probabilities
- **Surge Multiplier** = Dynamic pricing factor for that hour and zone
- **Weather Multiplier** = Demand adjustment based on weather conditions
- **Total Time** = Travel time + Expected wait time (calculated from demand rate)

**Transition Probabilities** are computed using Laplace smoothing:
```
P(i→j) = (trips_from_i_to_j[hour] + ε) / (total_trips_from_i[hour] + ε × |zones|)
```

### 4. Dynamic Programming Optimization

The core algorithm uses **backward induction** to find the optimal strategy:

```python
V[time_remaining][cluster] = max over all destinations j of:
    (fare_to_j × surge × weather) + γ × V[time_remaining - trip_time][j]
```

**Parameters**:
- `γ` (gamma) = 0.95 (discount factor for future earnings)
- `time_remaining` = Minutes left in the work shift
- `trip_time` = Travel time + wait time at destination

**The algorithm**:
1. Starts with terminal condition: `V[0][any_cluster] = 0` (no time left = no earnings)
2. Works backward through time intervals (5-minute increments)
3. For each cluster and time, finds the best next destination
4. Stores the optimal path and expected total earnings

**Result**: For a given start hour and work duration, the system identifies:
- Which zone to start in (highest expected earnings)
- The optimal sequence of zones to move through
- Total expected earnings for the shift

---

## 🔌 API Endpoints

### Driver Preferences

#### Set Working Hours
```http
POST /api/v1/drivers/{driver_id}/preferences
Content-Type: application/json

{
  "earliest_start_time": "06:00",
  "latest_start_time": "18:00",
  "nr_hours": 8
}
```
Stores the driver's preferred working time window and shift duration.

#### Get Working Hours
```http
GET /api/v1/drivers/{driver_id}/preferences
```
Retrieves saved preferences.

### Recommendations

#### Get Optimal Start Time
```http
GET /api/v1/drivers/{driver_id}/recommendations/optimal-time
```
Returns the **best start time** within the driver's preferred window, along with:
- Expected score (earnings potential)
- Remaining hours available to work

#### Get All Time Scores
```http
GET /api/v1/drivers/{driver_id}/recommendations/time-scores
```
Returns a **list of all possible start times** with their comparative scores, used to generate the histogram visualization showing earnings potential for each hour.

#### Get Best Zone for a Time
```http
GET /api/v1/drivers/{driver_id}/recommendations/best-zone?current_time=8
```
Returns the **optimal starting zone** for a specific hour, including:
- Cluster ID
- Expected score
- Center coordinates for map display

#### Get All Zone Scores
```http
GET /api/v1/drivers/{driver_id}/recommendations/zone-scores
```
Returns **all zones ranked by score** for the selected time, enabling comparison visualization.

### AI Wellness Features

#### Chat with AI Assistant
```http
POST /api/v1/ai/chat/{driver_id}
Content-Type: application/json

{
  "message": "Should I take a break now?",
  "chat_history": []
}
```
Powered by **Google Gemini 2.5 Flash**, the AI assistant provides:
- Driving advice based on real-time conditions
- Wellness recommendations
- Tips for maximizing earnings
- Safety guidance

#### Get Wellness Reminder
```http
GET /api/v1/ai/wellness/{driver_id}?hours_driven=4.5
```
Automatically triggers a **break reminder after 4.5 hours** of active driving, promoting driver safety and well-being.

#### Driving Session Tracking
```http
POST /api/v1/drivers/{driver_id}/start-session  # Start tracking
POST /api/v1/drivers/{driver_id}/stop-session   # Stop tracking
GET /api/v1/drivers/{driver_id}/driving-hours   # Get current hours
```
Tracks driving sessions to automatically calculate hours driven for wellness features.

---

## 🎨 User Experience Flow

### 1. **Schedule Setup**
- Driver opens the app and clicks "Schedule Your Drive"
- Selects their preferred **start time window** (e.g., 06:00 - 18:00)
- Adjusts **total work hours** (e.g., 8 hours)
- System calculates the **optimal start time** using dynamic programming

### 2. **Time Comparison View**
- Driver sees a **bar chart histogram** showing:
  - All possible start times
  - Expected earnings as percentages relative to the optimal time
  - Color coding: Green (>66%), Orange (33-66%), Gray (<33%)
- Can scroll through and **select a different start time** if preferred
- Confirms selection to proceed

### 3. **Zone Selection**
- System displays the **recommended optimal zone** for the chosen time
- Driver can tap to see **zone comparison histogram**:
  - All zones ranked by expected earnings
  - Percentage scores relative to the best zone
  - Visual comparison to help make informed decisions
- Can explore alternative zones while seeing performance trade-offs

### 4. **Main Map Screen**
- After confirming time and zone:
  - Selected zone is **highlighted on the map**
  - Driver sees their current location
  - Real-time zone boundaries displayed
  - Start driving from the optimal location

### 5. **AI Wellness Copilot**
- **Proactive Break Reminder**: After **4.5 hours** of continuous driving, a modal appears:
  - "Time for a Break" notification
  - Option to open the Wellness Copilot chatbot
  - Can dismiss or engage with AI for break suggestions

- **AI Chat Features**:
  - Ask questions about driving strategy
  - Get wellness tips and break recommendations
  - Receive context-aware advice based on:
    - Current weather conditions
    - Surge pricing patterns
    - Recent trip performance
    - Driver preferences

### 6. **Real-time Features**
- Live driving hour counter
- Driver status indicator (Online/Offline)
- AI-generated suggestions based on:
  - Time of day (rush hours, late night patterns)
  - Weather conditions
  - Active surge zones
  - Recent performance

---

## 🏗️ Tech Stack

### Client
- **Bun** + **Expo** + **React Native** + **TypeScript**
- Cross-platform: iOS, Android, Web
- **React Navigation** for screens
- **Mapbox** for map visualization
- ESLint, Prettier for code quality
- Jest for unit testing

### Server
- **FastAPI** (Python 3.11+)
- **NetworkX** for graph operations
- **Pandas** for data processing
- **scikit-learn** (DBSCAN clustering)
- **Google Gemini 2.5 Flash** for AI chat
- **SQLite** for persistent storage
- **Redis** for caching and real-time data
- **Hatch** for environment management
- **Ruff** for linting & formatting

---

## 📁 Key Files

### Backend Core
- `server/app/cluster_analysis.py` - DBSCAN clustering implementation
- `server/app/graph_builder.py` - Builds city-hour mobility graphs
- `server/app/dynamic_programming_optimizer.py` - DP optimization algorithm
- `server/app/service.py` - Business logic layer
- `server/app/endpoints.py` - REST API endpoints
- `server/app/ai_agent.py` - AI chatbot and wellness features

### Frontend Core
- `client/screens/MapHomeScreen.tsx` - Main map interface
- `client/components/SchedulePanel.tsx` - Working hours selection
- `client/components/OptimalDetailsPanel.tsx` - Time/zone comparison histograms
- `client/components/WellnessNudge.tsx` - Break reminder modal
- `client/screens/AIChatScreen.tsx` - AI assistant chat
- `client/config/Config.ts` - API configuration

---

## 🎯 Features

✅ **Smart Scheduling**: ML-powered optimal time recommendations
✅ **Zone Optimization**: Dynamic programming for best starting locations
✅ **Visual Comparisons**: Interactive histograms for time/zone analysis
✅ **AI Copilot**: Context-aware chatbot for driving advice
✅ **Wellness Tracking**: Automatic break reminders after 4.5 hours
✅ **Real-time Data**: Surge pricing, weather, and demand integration
✅ **Session Tracking**: Automatic driving hours calculation
✅ **Map Visualization**: Highlighted zones and cluster boundaries
✅ **Multi-city Support**: Independent graphs and recommendations per city
✅ **Caching System**: Redis caching for fast DP computations

---

## 📊 Data Flow

1. **Historical Data** → DBSCAN Clustering → **Zone Graph**
2. **Zone Graph** + Weather + Surge → **Earning Rates**
3. **Earning Rates** + DP Algorithm → **Optimal Strategies**
4. **Driver Preferences** + Optimal Strategies → **Recommendations**
5. **Real-time Conditions** + AI → **Proactive Suggestions**

---

## 🔐 Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
REDIS_URL=redis://localhost:6379
DATABASE_URL=sqlite:///./data/app.db
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

---

## 📈 Performance Optimizations

- **Singleton Pattern**: Graph loaded once and reused
- **Graph Serialization**: Cached to disk for fast startup
- **Redis Caching**: DP results cached with 1-hour TTL
- **Transition Probability Caching**: Per (city, hour) to avoid recomputation
- **5-minute Time Intervals**: Balance between precision and speed

---

## 📝 License

This project was developed for the JunctionX Uber Challenge hackathon.

---

## 👥 Contributing

This is a hackathon project. For questions or issues, please contact the development team.

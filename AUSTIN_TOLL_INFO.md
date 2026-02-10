# Austin Area Toll Road Information

## Austin Major Highways Overview

### Free Highways
- **I-35** - Main interstate through Austin - **NO TOLLS**
- **I-35 Frontage Roads** - Free access roads parallel to I-35
- **US-183 (Regular lanes)** - Free regular lanes
- **MoPac/Loop 1 (Regular lanes)** - Free regular lanes (express lanes have tolls)
- **US-290 (Regular)** - Free regular lanes
- **TX-71 (Regular)** - Free regular lanes

### Toll/Express Lane Highways

#### 1. **183 Express/Toll** (US-183) ⚡ DYNAMIC PRICING
- **Type:** Express lanes / Toll lanes
- **Base Rate:** $0.65 per mile
- **Peak Rate:** Up to $1.30/mile (2x multiplier)
- **Off-Peak Rate:** As low as $0.39/mile (40% discount)
- **Description:** Express lanes on US-183 North
- **Coverage:** Manor to Cedar Park
- **Dynamic Pricing:** 
  - Morning rush (7:00 AM - 9:30 AM): Up to 2x
  - Evening rush (4:30 PM - 7:00 PM): Up to 2x
  - Off-peak (9:00 PM - 6:00 AM): 40% discount
  - Traffic congestion can add additional 40% surcharge

#### 2. **SH-45 Toll**
- **Type:** Full toll road
- **Rate:** $0.47 per mile (FIXED)
- **Description:** State Highway 45 connecting southwest to southeast Austin
- **Coverage:** MoPac to I-35
- **Alternative:** Free routes via US-290 or FM roads
- **Pricing:** Fixed rate, no dynamic pricing

#### 3. **MoPac Express** (Loop 1) ⚡ DYNAMIC PRICING
- **Type:** Express lanes only (regular lanes are free)
- **Base Rate:** $0.95 per mile
- **Peak Rat$0.17 per mile (FIXED)
- **Description:** Eastern bypass around Austin
- **Coverage:** Georgetown to Seguin
- **Speed Limit:** 85 mph (fastest in US)
- **Alternative:** I-35 (free but congested)
- **Pricing:** Fixed rate, no dynamic pricing

#### 5. **TX-71 Toll**
- **Type:** Toll lanes
- **Rate:** $0.50 per mile (FIXED)
- **Coverage:** Southwest Austin
- **Pricing:** Fixed rate, no dynamic pricing

#### 6. **Manor Expressway** (US-290 Toll)
- **Type:** Toll road
- **Rate:** $0.42 per mile (FIXED)
- **Coverage:** East Austin/Manor area
- **Pricing:** Fixed rate, no dynamic pricing
- **Description:** Eastern bypass around Austin
- **Coverage:** Georgetown to Seguin
- **Speed Limit:** 85 mph (fastest in US)
- **Alternative:** I-35 (free but congested)

#### 5. **TX-71 Toll**
- **Type:** Toll lanes
- **Rate:** ~$0.50 per mile
- **Coverage:** Southwest Austin

#### 6. **Manor Expressway** (US-290 Toll)
- **Type:** Toll road
- *Dynamic Toll Pricing System

### How Dynamic Pricing Works
**MoPac Express** and **183 Toll** use real-time congestion-based pricing:

#### Time-of-Day Rates
| Time Period | Multiplier | Example (MoPac Base $0.95) |
|-------------|-----------|----------------------------|
| **Peak (7-9:30 AM, 4:30-7 PM)** | 2.0-2.5x | $1.90 - $2.38/mile |
| **Mid-day (11 AM - 2 PM)** | 1.3x | $1.24/mile |
| **Regular (other times)** | 1.0x | $0.95/mile |
| **Off-peak (9 PM - 6 AM)** | 0.6x | $0.57/mile |

#### Congestion Surcharge
- When traffic is **30% slower than expected**, an additional **40% surcharge** applies
- This simulates real-world dynamic pricing during heavy congestion
- Applied on top of time-of-day rates (capped at peak multiplier)

### Static vs Dynamic Toll Roads
- **Dynamic:** MoPac Express, 183 Toll (price changes by time/traffic)
- **Fixed:** SH-45, SH-130, TX-71, Manor Expressway (constant rate)
- **MoPac Express** uses dynamic congestion pricing
- Rates vary from $0.25 to $1.50+ per mile depending on traffic
- Our app uses average rates for estimation

### Distance-Based Calculation
The Austin Toll Service calculates tolls by:
1. Detecting which highways are used in each route
2. Measuring distance on each toll segment
3. Applying per-mile rates for each toll road
4. Summing total toll cost
Dynamic Pricing Implementation
- **Time-based rates:** Automatically adjusts based on current time
- **Congestion detection:** Uses route ETA vs. expected time to detect slow traffic
- **Peak multipliers:** MoPac up to 2.5x, 183 Toll up to 2.0x during rush hour
- **Off-peak discounts:** 40% discount late night/early morning (9 PM - 6 AM)
- **Does not include:** TxTag/EZ Tag subscriber discounts, weekend special rat-----|------|
| I-35 | Baseline | Baseline | +50-100% | $0.00 |
| SH-130 | +30 mi | Same/Faster | Much Faster | $5-8 |
| Toll combo | Similar | 20-30% faster | 40-60% faster | $8-15 |

## Route Optimization Strategy

The Toll Budget Routing app:
1. **Identifies toll-free routes** (I-35 only) - displayed first
2. **Finds fastest overall route** (ignoring budget) - shown for comparison
3. **Optimizes within budget** - finds fastest route that fits your toll budget
4. **Ranks by speed** - within budget, faster routes ranked higher

## Accuracy Notes

### Real-Time Limitations
- Toll rates are averages (actual rates vary by time of day)
- Does not include TxTag/EZ Tag discounts
- Peak hour pricing can be 2-3x higher on express lanes

### Road Detection
- Uses Mapbox routing with road name detection
- Falls back to distance-based estimation if road names unavailable
- Continuously improved with more detailed road segment data

## For Developers

See `services/austin_toll_service.py` for implementation details and toll rate adjustments.

To update toll rates:
1. Edit `TOLL_ROADS` dictionary in `austin_toll_service.py`
2. Adjust `rate_per_mile` values
3. No restart needed (uvicorn auto-reloads)

# VayuDrishti (??????????)
### Real-Time Airfare Price Index & CPI Augmentation Platform
**Ministry of Statistics and Programme Implementation (MoSPI), Government of India**
**Smart India Hackathon (SIH26056) | Category: Software / Smart Automation**

---

## 1. Executive Summary & Problem Overview
The **Consumer Price Index (CPI)** is India's principal benchmark for measuring retail inflation and formulating monetary policy by the Reserve Bank of India (RBI). In the transport & communication group (weight: **8.59%**), civil aviation fares are among the most volatile components due to airline algorithmic yield management, dynamic surge pricing, festive spikes, and varying booking horizons ($D-0$ to $D-60$).

Traditional survey-based monthly CPI data collection experiences:
1. **Severe Time Lag**: 12-15 day delay post-month-end.
2. **Sampling Bias**: Fails to capture multi-horizon dynamic pricing.
3. **Amenity Confounding**: Cannot isolate pure price inflation from baggage, duration, or routing shifts.

**VayuDrishti (??????????)** solves this by creating an automated, national statistical office (NSO) grade pipeline that ingests real-time fares across 100+ corridors and 7 booking horizons, computes quality-adjusted price indices (**Jevons, DGCA-weighted Laspeyres, Hedonic OLS Regression**), and provides high-frequency CPI transport augmentation feeds.

---

## 2. Key Architecture & Features

```
+--------------------------------------------------------------------------------+
|                           VayuDrishti Architecture                             |
+--------------------------------------------------------------------------------+
| [1. Ingestion Engine]     IndiGo | Air India | Akasa | SpiceJet | MMT | EaseMyTrip |
| [2. Sanitization]        Tukey IQR Fences, Modified Z-score, 99th Winsorization |
| [3. Statistical Engine]  DGCA-Weighted Laspeyres, Jevons Mean, Hedonic OLS     |
| [4. CPI Augmentation]    Transport Sub-Index Augmentation & RBI MPC Nowcast   |
| [5. MoSPI Portal]        Live Ticker, GIS Corridors, Policy Sandbox, Gazette   |
+--------------------------------------------------------------------------------+
```

1. **Multi-Source Scraping & Sampling Grid**:
   - Monitored Carriers: IndiGo, Air India Group, Akasa Air, SpiceJet.
   - Monitored OTAs: MakeMyTrip, EaseMyTrip, Google Flights.
   - Corridors: 100+ representative routes across Metro-Metro, Metro-Tier2, UDAN RCS, and Hill/Island strategic sectors.
   - Lead Times: $D-0, D-1, D-3, D-7, D-15, D-30, D-60$.

2. **Statistical Index Formulations**:
   - **DGCA-Weighted Laspeyres Index**:
     $$I_{\text{Laspeyres}}^t = \sum_{r} w_r \left( \sum_{a} s_a \frac{P_{r,a,t}}{P_{r,a,0}} \right) \times 100$$
   - **Jevons Elementary Aggregate**:
     $$I_{\text{Jevons}}^t = \exp\left( \frac{1}{N} \sum_{i=1}^N \ln\left(\frac{P_{i,t}}{P_{i,0}}\right) \right) \times 100$$
   - **Hedonic Log-Linear Quality Regression**:
     $$\ln(P_{i,t}) = \beta_0 + \beta_{\text{dur}}\text{Duration} + \beta_{\text{stops}}\text{Stops} + \beta_{\text{lead}}\ln(\text{Lead}+1) + \beta_{\text{bag}}\text{Baggage} + \sum \gamma_c \text{Carrier}_c + \epsilon_{i,t}$$

3. **Policy Simulation Sandbox**:
   - Simulates Aviation Turbine Fuel (ATF) excise duty changes, emergency fare caps, UDAN VGF subsidies, and holiday demand surges on CPI headline basis points.

4. **MoSPI Gazetted Bulletin & SDMX Feeds**:
   - One-click export of official publication-grade PDF bulletins and UN/IMF JSON-stat feeds.

---

## 3. Quick Start & Execution

### Prerequisites
- Python 3.11+ (FastAPI, Pandas, NumPy, Scipy, ReportLab)

### Launch the Application
```bash
python run_app.py
```
Open **`http://localhost:8000`** in your browser to access the live MoSPI Command Center.

### Run Unit Tests
```bash
python backend/tests/test_indices.py
```

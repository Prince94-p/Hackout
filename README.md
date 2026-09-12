🌱 CarbonCore

Detect. Diagnose. Divert. Decarbonize.

CarbonCore is an industrial carbon-intelligence and circular-economy decision-support platform built for Small and Medium Enterprises (SMEs).

Most carbon calculators stop after answering:

“How much carbon are we emitting?”

CarbonCore goes further and helps answer:

Where are the emissions coming from? Why are they happening? What can we improve? What will it save? And what should we implement first?

⸻

🏆 HackOut’26

Team: TechVortex
Project: CarbonCore
Domain: Industrial Sustainability • Carbon Intelligence • Circular Economy

CarbonCore was built as a solution for industries that need a practical way to understand their emissions and convert carbon data into measurable operational actions.

⸻

🚨 Problem

Small and medium industries generate emissions through several operational activities:

* ⚡ Electricity and energy consumption
* 🧱 Raw materials
* 🏭 Manufacturing processes
* 🗑️ Industrial waste
* 💨 Operational inefficiencies
* ♻️ Poor resource recovery and reuse

The problem is not only measuring the total carbon footprint.

Industries need to understand:

1. Which source contributes the most emissions?
2. Why is that source producing high emissions?
3. Which circular intervention can reduce it?
4. How much CO₂ can potentially be saved?
5. What could implementation cost?
6. Which action should be prioritized first?

⸻

💡 Our Solution

CarbonCore transforms raw factory activity data into an actionable decarbonization strategy.

Factory Data
     ↓
Carbon Calculation
     ↓
Emission Hotspot Detection
     ↓
Root-Cause Analysis
     ↓
Circular Recommendations
     ↓
Scenario Simulation
     ↓
Prioritized Roadmap
     ↓
ACTION

From carbon accounting to carbon decision intelligence.

⸻

✨ Key Features

🏭 Factory Setup

Create and configure a factory profile with relevant operational information.

CarbonCore supports data related to:

* Energy
* Materials
* Processes
* Waste
* Industrial activity

⸻

📊 Carbon Intelligence Dashboard

The dashboard converts raw activity data into clear emission insights.

Users can understand:

* Total carbon footprint
* Energy contribution
* Material contribution
* Waste contribution
* Process-level emissions
* Major emission hotspots

⸻

🔍 Carbon Leak Detector

CarbonCore highlights processes where carbon emissions or resource usage appear unusually high.

Example:

High Electricity Consumption
          ↓
Compressed Air System
          ↓
Potential Operational Inefficiency
          ↓
Carbon Hotspot

This helps businesses identify where efficiency improvements may have the greatest impact.

⸻

🧠 Root-Cause Analysis

Detecting a hotspot is only the first step.

CarbonCore also helps explain why the problem may be occurring.

Example:

Compressed Air Hotspot
        ↓
Possible Causes
        ↓
• Air leakage
• Excess operating pressure
• Inefficient sequencing
• Maintenance issues

This connects emission data with real operational causes.

⸻

♻️ Circular Solutions

CarbonCore maps identified problems to potential circular and efficiency interventions.

Possible interventions include:

* Material substitution
* Recycling loops
* Waste recovery
* Resource reuse
* Process optimization
* Energy-efficiency improvements
* Compressed-air leak remediation
* Pressure optimization
* Equipment sequencing

⸻

🧪 What-If Scenario Simulator

Businesses can explore the potential result of an intervention before implementing it.

Users can adjust scenario assumptions such as:

* Implementation percentage
* Expected performance
* Cost variation

The simulator estimates:

* Potential CO₂ reduction
* Estimated implementation cost
* Approximate payback impact

Choose Intervention
       ↓
Adjust Parameters
       ↓
Run Scenario
       ↓
CO₂ Saving + Cost + Impact

⸻

🗺️ Decarbonization Roadmap

CarbonCore converts recommendations into a prioritized action roadmap.

Instead of presenting a long list of suggestions, the roadmap helps answer:

“What should we implement first?”

Actions can be prioritized using:

* Carbon reduction potential
* Cost
* Operational feasibility
* Expected benefit
* Implementation impact

⸻

📥 CSV Data Workflow

CarbonCore supports structured factory data workflows through:

* Manual data entry
* CSV import
* CSV template
* Input validation
* Roadmap export

This allows industries to work with structured operational datasets instead of only demonstration values.

⸻

🔄 User Journey

Landing Page
      ↓
Login / Registration
      ↓
Factory Setup
      ↓
Factory Data
      ↓
Carbon Overview
      ↓
Leak Detector
      ↓
Root Cause
      ↓
Circular Solutions
      ↓
Scenario Simulator
      ↓
Action Roadmap

Stage	Main Question
Factory Data	What are we consuming?
Carbon Overview	Where are emissions coming from?
Leak Detector	Where are we inefficient?
Root Cause	Why is it happening?
Solutions	What can we change?
Simulator	What happens if we change it?
Roadmap	What should we do first?

⸻

🧮 Carbon Calculation

CarbonCore uses an activity-based calculation model:

CO₂e = Activity Data × Emission Factor

Example

Electricity Consumption
= 1,250,000 kWh
Emission Factor
= 0.48 kgCO₂e/kWh
Emissions
= 1,250,000 × 0.48
= 600,000 kgCO₂e
= 600 tCO₂e

⸻

🏭 Demo Factory

The prototype includes a demonstration dataset for:

Apex Components Pvt. Ltd.

Industry: Automotive Manufacturing
Location: Gujarat, India

Source	Estimated Emissions
⚡ Energy	600 tCO₂e
🧱 Materials	400 tCO₂e
🗑️ Waste	150 tCO₂e
Total	1,150 tCO₂e/year

This allows judges to explore the complete CarbonCore workflow immediately.

⸻

⚙️ Tech Stack

Frontend

* HTML5
* JavaScript
* Tailwind CSS 4
* Vite
* Chart.js
* Lucide Icons
* Manrope
* DM Sans

Backend / Application Architecture

* Python backend modules
* Structured routers
* Schemas
* Service layer
* Carbon calculation logic
* Hotspot analysis
* Recommendation logic
* Roadmap logic

Testing

* Automated tests
* Playwright browser testing
* Node test runner
* Input validation

⸻

🏗️ Architecture

┌──────────────────────────────┐
│          Frontend            │
│                              │
│ Forms • Dashboard • Charts   │
│ Simulator • Roadmap          │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│      Application Layer       │
│                              │
│ State • API • Validation     │
│ Navigation • Data Handling   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   Carbon Intelligence Layer  │
│                              │
│ Carbon Calculation           │
│ Hotspot Detection            │
│ Root-Cause Analysis          │
│ Recommendations              │
│ Scenario Simulation          │
│ Roadmap Generation           │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│           Data Layer         │
│                              │
│ Factory • Activities         │
│ Scenarios • Results          │
└──────────────────────────────┘

⸻

📁 Project Structure

Hackout/
│
├── backend/
├── docs/
├── public/
├── src/
│   ├── css/
│   └── js/
│
├── tests/
│
├── index.html
├── login.html
├── register.html
├── factory-setup.html
├── factory-data.html
├── dashboard.html
├── leak-detector.html
├── root-cause.html
├── solutions.html
├── simulator.html
├── roadmap.html
│
├── package.json
├── package-lock.json
├── vite.config.js
├── playwright.config.js
├── .gitignore
└── README.md

⸻

🚀 Run Locally

1. Clone

git clone https://github.com/Prince94-p/Hackout.git
cd Hackout

2. Install Dependencies

npm install

3. Start Development Server

npm run dev

Open the Vite URL shown in the terminal.

Usually:

http://127.0.0.1:5173

⸻

🧪 Testing

Run automated tests:

npm test

Install Playwright Chromium:

npx playwright install chromium

Run browser tests:

npm run test:browser

Production build:

npm run build

Preview:

npm run preview

⸻

🎯 Why CarbonCore?

Traditional Carbon Calculator

INPUT
  ↓
CALCULATE
  ↓
TOTAL FOOTPRINT
  ↓
END

CarbonCore

INPUT
  ↓
HOW MUCH?
  ↓
FROM WHERE?
  ↓
WHY?
  ↓
WHAT CAN WE CHANGE?
  ↓
WHAT COULD IT SAVE?
  ↓
WHAT COULD IT COST?
  ↓
WHAT SHOULD WE DO FIRST?
  ↓
ACTION

The core innovation is the transition from:

Carbon Measurement → Carbon Decision Intelligence

⸻

🌍 Expected Impact

CarbonCore can help SMEs:

Understand their major emission sources.

Detect operational inefficiencies.

Diagnose potential root causes.

Discover circular and lower-carbon alternatives.

Simulate interventions before implementation.

Prioritize actions according to potential impact.

Build a practical decarbonization roadmap.

⸻

🔮 Future Scope

CarbonCore can evolve further through:

* 🤖 AI/ML recommendation models
* 📚 Verified emission-factor databases
* 📡 IoT energy-meter integration
* 🏭 ERP integration
* 🌍 Scope 1, Scope 2 and Scope 3 classification
* 🔗 Supplier carbon tracking
* 📈 Carbon forecasting
* 🏢 Multi-factory benchmarking
* 📑 Automated sustainability reports
* ⚖️ Regulatory reporting
* 🧠 Predictive root-cause analysis
* 💰 Cost-benefit optimization
* 🎯 Intelligent intervention ranking

⸻

⚠️ Prototype Disclaimer

CarbonCore is currently a HackOut’26 prototype.

Emission factors, savings, costs, payback values, confidence scores and demonstration datasets may contain illustrative assumptions intended to demonstrate the platform workflow.

They should not be treated as certified:

* Carbon-accounting results
* Regulatory calculations
* Live industrial measurements
* Financial projections

A production deployment would use verified emission-factor datasets, organization-specific operational information and relevant carbon-accounting standards.

⸻

👥 Team TechVortex

Built at HackOut’26 with one goal:

Make industrial sustainability understandable, measurable and actionable.

⸻

<div align="center">

🌱 CarbonCore

Detect the source. Understand the cause. Simulate the solution. Build the roadmap.

From Carbon Footprint → To Carbon Action

</div>

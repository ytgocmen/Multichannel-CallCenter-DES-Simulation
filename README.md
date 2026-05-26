# Multichannel Call Center Simulation using Discrete Event Simulation (DES)

## Project Overview

This project models a real-world **multichannel customer service center** (phone, email, live chat) using **Discrete Event Simulation (DES)**. The goal is to identify operational bottlenecks, quantify the impact of peak demand, and evaluate staffing improvement strategies — all in a risk-free virtual environment.

Built with **Python and SimPy**, the model incorporates stochastic customer arrivals, variable service times, and customer patience (reneging behaviour).

## The Problem

Static planning methods (e.g. spreadsheet averages) cannot capture the randomness of real operations. Customers don't arrive at fixed intervals — clusters and bursts cause queues to form even when average capacity *looks* sufficient. This simulation proves that with data.

## Three Scenarios Tested

| Scenario | Setup | Key Finding |
|---|---|---|
| **Baseline** | 2 phone + 1 email + 1 chat agent | Normal operations, manageable queues |
| **Peak Demand** | Same agents, +33% arrival rate | Up to **50% customer abandonment** |
| **Improvement** | 3 phone + 2 email + 2 chat agents | Wait times reduced by **~60%**, abandonment controlled |

## System Architecture

```
Customer Arrival (Poisson Process)
        │
        ▼
┌───────────────────┐
│  Channel Router   │
└───────────────────┘
   │         │         │
   ▼         ▼         ▼
Phone      Email     Live Chat
(180s avg) (900s avg) (120s avg)
(120s pat) (300s pat) (180s pat)
   │         │         │
   └────────►▼◄────────┘
        KPI Aggregator
   (Wait Time | Abandonment | Utilisation)
```

## Key Technical Features

- **Reneging behaviour** — customers abandon the queue if patience threshold is exceeded (`simpy.Resource` + timeout race)
- **Weighted system-wide KPIs** — metrics aggregated by channel volume and agent capacity, not simple averages
- **Dual execution modes** — `VERIFICATION_MODE=True` prints a full event log for model validation; `VERIFICATION_MODE=False` runs 50 replications and generates charts
- **Exponential distributions** — inter-arrival times (Poisson process) and service durations modelled with `random.expovariate`

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![SimPy](https://img.shields.io/badge/SimPy-DES-orange?style=flat)
![NumPy](https://img.shields.io/badge/NumPy-013243?style=flat&logo=numpy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-150458?style=flat&logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-11557c?style=flat)

## How to Run

```bash
# Install dependencies
pip install simpy numpy pandas matplotlib

# Run in verification mode (event log, 1 replication)
# Set VERIFICATION_MODE = True and REPLICATIONS = 1 in the script
python call_center_simulation.py

# Run in analysis mode (50 replications, charts)
# Set VERIFICATION_MODE = False and REPLICATIONS = 50 in the script
python call_center_simulation.py
```

## Key Results

- **Peak Demand** scenario caused abandonment rates exceeding **50%** with unchanged staffing
- **Improvement** scenario reduced system-wide average wait time by approximately **60%**
- Weighted KPI aggregation revealed that email channel masked phone bottlenecks in naive averages
- Model validated via full event-log trace confirming correct reneging, service, and departure logic

## Project Context

Developed as part of the **Simulation Techniques** module at Berlin School of Business and Innovation (2026). Demonstrates how DES can replace guesswork in operational planning with statistically reliable, scenario-tested recommendations.

import simpy
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# SETTINGS AND CONSTANTS
# ==========================================
RANDOM_SEED = 42
SIM_TIME = 8 * 60 * 60  # Simulation time in seconds (8 hours)

# Set REPLICATIONS = 50 and VERIFICATION_MODE = False for final analysis/graphs.
# Set REPLICATIONS = 1 and VERIFICATION_MODE = True to generate logs and prove model behavior to the instructor.
REPLICATIONS = 1
VERIFICATION_MODE = True

random.seed(RANDOM_SEED)

# ==========================================
# CLASSES AND FUNCTIONS
# ==========================================

class KPIs:
    def __init__(self):
        self.waiting_times = []
        self.abandoned = 0
        self.served = 0
        self.busy_time = 0

def customer(env, name, resource, service_time_func, patience, kpi):
    """
    Simulates the customer lifecycle: Arrival -> Queue/Reneging -> Service -> Departure
    """
    arrival_time = env.now

    if VERIFICATION_MODE:
        print(f"{env.now:8.2f} : {name} arrived at the system.")

    with resource.request() as request:
        # Request resource or wait until patience runs out
        result = yield request | env.timeout(patience)

        if request in result:
            # --- SERVICE STARTED ---
            wait = env.now - arrival_time
            kpi.waiting_times.append(wait)
            service_start = env.now

            if VERIFICATION_MODE:
                print(f"{env.now:8.2f} : {name} started service (Waited: {wait:.2f}s).")

            # Wait for the duration of the service
            duration = service_time_func()
            yield env.timeout(duration)

            kpi.busy_time += duration
            kpi.served += 1

            if VERIFICATION_MODE:
                print(f"{env.now:8.2f} : {name} completed service and left.")

        else:
            # --- ABANDONMENT (RENEGING) ---
            kpi.abandoned += 1
            if VERIFICATION_MODE:
                print(f"{env.now:8.2f} : {name} ran out of patience and abandoned the queue.")

def arrival_process(env, name, arrival_rate, resource, service_time_func, patience, kpi):
    """
    Generates customers according to an exponential inter-arrival time.
    """
    i = 0
    while True:
        yield env.timeout(random.expovariate(arrival_rate))
        i += 1
        cust_name = f"{name}_{i}"
        env.process(customer(env, cust_name, resource, service_time_func, patience, kpi))

def run_simulation(params):
    env = simpy.Environment()

    # KPI trackers for each channel
    phone_kpi = KPIs()
    email_kpi = KPIs()
    chat_kpi = KPIs()

    # Resources (Assuming Dedicated Agents per channel)
    phone_agents = simpy.Resource(env, capacity=params["phone_agents"])
    email_agents = simpy.Resource(env, capacity=params["email_agents"])
    chat_agents  = simpy.Resource(env, capacity=params["chat_agents"])

    # Start Processes
    # 1. Phone (Avg Service: 180s, Patience: 120s)
    env.process(arrival_process(
        env, "Phone", params["phone_arrival"], phone_agents,
        lambda: random.expovariate(1/180), 120, phone_kpi
    ))

    # 2. Email (Avg Service: 900s, Patience: 300s)
    env.process(arrival_process(
        env, "Email", params["email_arrival"], email_agents,
        lambda: random.expovariate(1/900), 300, email_kpi
    ))

    # 3. Chat (Avg Service: 180s, Patience: 180s)
    env.process(arrival_process(
        env, "Chat", params["chat_arrival"], chat_agents,
        lambda: random.expovariate(1/120), 180, chat_kpi
    ))

    env.run(until=SIM_TIME)

    return phone_kpi, email_kpi, chat_kpi

def calculate_channel_stats(kpi, capacity):
    """Calculates statistics for a single channel."""
    if kpi.served == 0 and kpi.abandoned == 0:
        return 0, 0, 0, 0

    avg_wait = np.mean(kpi.waiting_times) if kpi.waiting_times else 0
    total_calls = kpi.served + kpi.abandoned
    abandonment_rate = (kpi.abandoned / total_calls) * 100 if total_calls > 0 else 0
    utilisation = (kpi.busy_time / (SIM_TIME * capacity)) * 100 if capacity > 0 else 0

    return avg_wait, abandonment_rate, utilisation, total_calls

# ==========================================
# SCENARIOS
# ==========================================
SCENARIOS = {
    "Baseline": {
        "phone_arrival": 15/3600, "email_arrival": 7/3600, "chat_arrival": 10/3600,
        "phone_agents": 2, "email_agents": 1, "chat_agents": 1
    },
    "Peak Demand": {
        "phone_arrival": 20/3600, "email_arrival": 10/3600, "chat_arrival": 15/3600,
        "phone_agents": 2, "email_agents": 1, "chat_agents": 1
    },
    "Improvement": {
        "phone_arrival": 15/3600, "email_arrival": 7/3600, "chat_arrival": 10/3600,
        "phone_agents": 3, "email_agents": 2, "chat_agents": 2
    }
}

# ==========================================
# MAIN EXECUTION LOOP
# ==========================================
print(f"Simulation Starting... (Mode: {'VERIFICATION' if VERIFICATION_MODE else 'ANALYSIS'})")
results = []

for scenario, params in SCENARIOS.items():
    waits, abandons, utils = [], [], []

    if VERIFICATION_MODE:
        print(f"\n--- Scenario: {scenario} ---")
    for _ in range(REPLICATIONS):
        p_kpi, e_kpi, c_kpi = run_simulation(params)

        # Calculate stats for each channel
        pw, pa, pu, p_vol = calculate_channel_stats(p_kpi, params["phone_agents"])
        ew, ea, eu, e_vol = calculate_channel_stats(e_kpi, params["email_agents"])
        cw, ca, cu, c_vol = calculate_channel_stats(c_kpi, params["chat_agents"])

        # --- WEIGHTED AVERAGE (SYSTEM WIDE PERFORMANCE) ---
        # Weighting Wait Time and Abandonment by Volume
        total_vol = p_vol + e_vol + c_vol

        if total_vol > 0:
            avg_wait_system = (pw*p_vol + ew*e_vol + cw*c_vol) / total_vol
            avg_abandon_system = (pa*p_vol + ea*e_vol + ca*c_vol) / total_vol
        else:
            avg_wait_system = 0
            avg_abandon_system = 0

        # Weighting Utilisation by Capacity (Number of Agents)
        total_agents = params["phone_agents"] + params["email_agents"] + params["chat_agents"]
        avg_util_system = ((pu * params["phone_agents"]) +
                           (eu * params["email_agents"]) +
                           (cu * params["chat_agents"])) / total_agents

        waits.append(avg_wait_system)
        abandons.append(avg_abandon_system)
        utils.append(avg_util_system)

    results.append([
        scenario,
        np.mean(waits),
        np.mean(abandons),
        np.mean(utils)
    ])

# ==========================================
# RESULTS AND VISUALIZATION
# ==========================================
if not VERIFICATION_MODE:
    df = pd.DataFrame(
        results,
        columns=["Scenario", "Avg Wait (s)", "Abandonment (%)", "Utilisation (%)"]
    )

    print("\n--- SIMULATION RESULTS (System Wide Average) ---")
    print(df.round(2))

    # Plotting
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))

    # 1. Waiting Time
    ax[0].bar(df["Scenario"], df["Avg Wait (s)"], color=['blue', 'red', 'green'])
    ax[0].set_title("Average Waiting Time (System Wide)")
    ax[0].set_ylabel("Seconds")

    # 2. Abandonment Rate
    ax[1].bar(df["Scenario"], df["Abandonment (%)"], color=['blue', 'red', 'green'])
    ax[1].set_title("Abandonment Rate (%)")
    ax[1].set_ylabel("Percentage")

    # 3. Utilisation
    ax[2].bar(df["Scenario"], df["Utilisation (%)"], color=['blue', 'red', 'green'])
    ax[2].set_title("Resource Utilisation (%)")
    ax[2].set_ylabel("Percentage")

    plt.tight_layout()
    plt.show()

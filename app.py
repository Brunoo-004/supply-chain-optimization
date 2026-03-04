import streamlit as st
import pyomo.environ as pyo
import pandas as pd
import os
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Logistics Network Optimizer", layout="wide")

st.title("🚚 Supply Chain Network Optimization")
st.markdown("""
This application analyzes the financial impact of expanding Distribution Center (DC) capacity.
It uses **Linear Programming (GLPK Solver)** to find the global minimum for freight costs.
""")
st.markdown("---")

# --- SIDEBAR: CONTROLS & INPUTS ---
st.sidebar.header("⚙️ Scenario Settings")

DEFAULT_FILE = "Base_Dados_Exercicio_Rotas.xlsx"
data_source = None

if os.path.exists(DEFAULT_FILE):
    data_source = DEFAULT_FILE
    st.sidebar.success(f"✅ Loaded default case study: {DEFAULT_FILE}")
else:
    uploaded = st.sidebar.file_uploader("Upload Supply Chain Data (Excel)", type=["xlsx"])
    if uploaded:
        data_source = uploaded

st.sidebar.subheader("Financial & Operational Inputs")
capex_input = st.sidebar.number_input("Expansion Investment (CAPEX $)", min_value=0, value=50000, step=1000)
op_days_month = st.sidebar.slider("Operating Days per Month", min_value=1, max_value=31, value=22)

st.sidebar.subheader("Capacity Constraints")
cap_cd_slider = st.sidebar.slider("Current DC Capacity Simulation (t)", min_value=120, max_value=500, value=240)

# --- OPTIMIZATION ENGINE ---
def run_optimization(df_costs, df_data, target_dc_cap):
    origins = list(df_costs.index)
    destinations = list(df_costs.columns)
    
    capacities = df_data['Capacidade'].to_dict()
    capacities['CD'] = target_dc_cap
    
    demands = df_data.loc['Demanda', destinations].to_dict()
    freight_costs = df_costs.stack().to_dict()

    model = pyo.ConcreteModel()
    model.Origins = pyo.Set(initialize=origins)
    model.Destinations = pyo.Set(initialize=destinations)
    model.x = pyo.Var(model.Origins, model.Destinations, within=pyo.NonNegativeReals)
    
    def obj_rule(model):
        return sum(freight_costs[i, j] * model.x[i, j] for i in model.Origins for j in model.Destinations)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(model, i):
        return sum(model.x[i, j] for j in model.Destinations) <= capacities[i]
    model.cap_constraint = pyo.Constraint(model.Origins, rule=cap_rule)

    def dem_rule(model, j):
        return sum(model.x[i, j] for i in model.Origins) == demands[j]
    model.dem_constraint = pyo.Constraint(model.Destinations, rule=dem_rule)

    solver = pyo.SolverFactory('glpk')
    solver.solve(model)
    
    routes = []
    for i in model.Origins:
        for j in model.Destinations:
            val = pyo.value(model.x[i, j])
            if val > 0:
                total_dest_demand = demands[j]
                share_pct = (val / total_dest_demand) * 100
                routes.append({
                    'From': i, 'To': j, 'Qty (t)': round(val, 2), 
                    'Cost ($)': round(val * freight_costs[i,j], 2),
                    'Market Share (%)': f"{share_pct:.1f}%"
                })
    
    return pyo.value(model.obj), pd.DataFrame(routes)

# --- MAIN LOGIC ---
if data_source is not None:
    try:
        df_costs = pd.read_excel(data_source, sheet_name="Custo Frete", index_col=0)
        df_data = pd.read_excel(data_source, sheet_name="Matriz de Decisões", index_col=0)

        # Optimization runs
        baseline_cost, _ = run_optimization(df_costs, df_data, 120)
        optimized_cost, df_routes = run_optimization(df_costs, df_data, cap_cd_slider)

        # Calculations
        daily_savings = baseline_cost - optimized_cost
        monthly_savings = daily_savings * op_days_month
        payback_months = capex_input / monthly_savings if monthly_savings > 0 else 0

        # --- SECTION 1: EXECUTIVE SUMMARY ---
        st.subheader("📊 Strategic Performance Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Baseline Daily Cost", f"$ {baseline_cost:,.2f}")
        m2.metric("Optimized Daily Cost", f"$ {optimized_cost:,.2f}", delta=f"- $ {daily_savings:,.2f}")
        m3.metric("Estimated Monthly Savings", f"$ {monthly_savings:,.2f}", help="Based on operating days")
        m4.metric("Payback Period", f"{payback_months:.1f} Months" if payback_months > 0 else "N/A")

        # --- SECTION 2: DEEP DIVE - SENSITIVITY ANALYSIS ---
        st.markdown("---")
        st.subheader("🔍 Deep Dive: Capacity Saturation Analysis")
        st.write("This analysis shows the impact of DC expansion on total costs to find the optimal investment point.")
        
        # Run sensitivity analysis automatically
        cap_range = np.arange(120, 520, 20)
        sens_results = []
        for c in cap_range:
            cost, _ = run_optimization(df_costs, df_data, c)
            sens_results.append({'Capacity': c, 'Total Cost': cost})
        
        df_sens = pd.DataFrame(sens_results)
        
        col_chart, col_data = st.columns([2, 1])
        with col_chart:
            st.line_chart(df_sens, x='Capacity', y='Total Cost', color="#29b5e8")
        with col_data:
            st.write("Current Scenario Route Map")
            st.dataframe(df_routes[['From', 'To', 'Qty (t)', 'Market Share (%)']], height=250)

        st.info(f"💡 **Insight:** Beyond a certain capacity, the cost curve flattens. This is the **Saturation Point** where additional investment yields no further freight savings.")

    except Exception as e:
        st.error(f"Execution Error: {e}")
else:
    st.warning("👈 Awaiting data input. Please provide the Excel database to proceed.")

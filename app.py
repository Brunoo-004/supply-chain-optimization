import streamlit as st
import pyomo.environ as pyo
import pandas as pd
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Logistics Network Optimizer", layout="wide")

st.title("🚚 Supply Chain Network Optimization")
st.markdown("""
This application analyzes the financial impact of expanding Distribution Center (DC) capacity.
It utilizes **Linear Programming (GLPK Solver)** to minimize total daily freight costs.
""")
st.markdown("---")

# --- SIDEBAR: CONTROLS & INPUTS ---
st.sidebar.header("⚙️ Scenario Settings")

# 1. DATA LOADING LOGIC
DEFAULT_FILE = "Base_Dados_Exercicio_Rotas.xlsx"
data_source = None

if os.path.exists(DEFAULT_FILE):
    data_source = DEFAULT_FILE
    st.sidebar.success(f"✅ Loaded default case study: {DEFAULT_FILE}")
else:
    uploaded = st.sidebar.file_uploader("Upload Supply Chain Data (Excel)", type=["xlsx"])
    if uploaded:
        data_source = uploaded

# 2. FINANCIAL & OPERATIONAL PARAMETERS
st.sidebar.subheader("Financial & Operational Inputs")
capex_input = st.sidebar.number_input("Expansion Investment (CAPEX $)", min_value=0, value=50000, step=1000)
op_days_month = st.sidebar.slider("Operating Days per Month", min_value=1, max_value=31, value=22)

# 3. OPTIMIZATION CONSTRAINTS
st.sidebar.subheader("Capacity Constraints")
cap_cd_slider = st.sidebar.slider("New DC Capacity (t)", min_value=120, max_value=500, value=240)

# --- OPTIMIZATION ENGINE ---
def run_optimization(df_costs, df_data, target_dc_cap):
    origins = list(df_costs.index)
    destinations = list(df_costs.columns)
    
    # Map capacities and demands
    capacities = df_data['Capacidade'].to_dict()
    capacities['CD'] = target_dc_cap
    
    demands = df_data.loc['Demanda', destinations].to_dict()
    freight_costs = df_costs.stack().to_dict()

    # Model definition
    model = pyo.ConcreteModel()
    model.Origins = pyo.Set(initialize=origins)
    model.Destinations = pyo.Set(initialize=destinations)
    model.x = pyo.Var(model.Origins, model.Destinations, within=pyo.NonNegativeReals)
    
    # Objective: Minimize total cost
    def obj_rule(model):
        return sum(freight_costs[i, j] * model.x[i, j] for i in model.Origins for j in model.Destinations)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Constraints: Capacity & Demand
    def cap_rule(model, i):
        return sum(model.x[i, j] for j in model.Destinations) <= capacities[i]
    model.cap_constraint = pyo.Constraint(model.Origins, rule=cap_rule)

    def dem_rule(model, j):
        return sum(model.x[i, j] for i in model.Origins) == demands[j]
    model.dem_constraint = pyo.Constraint(model.Destinations, rule=dem_rule)

    # Solver execution
    solver = pyo.SolverFactory('glpk')
    solver.solve(model)
    
    # Results extraction and share calculation
    routes = []
    for i in model.Origins:
        for j in model.Destinations:
            val = pyo.value(model.x[i, j])
            if val > 0:
                # Calculate the percentage of customer demand fulfilled by this origin
                total_dest_demand = demands[j]
                share_pct = (val / total_dest_demand) * 100
                
                routes.append({
                    'From': i, 
                    'To': j, 
                    'Qty (t)': round(val, 2), 
                    'Cost ($)': round(val * freight_costs[i,j], 2),
                    'Market Share (%)': f"{share_pct:.1f}%"
                })
    
    return pyo.value(model.obj), pd.DataFrame(routes)

# --- DASHBOARD LAYOUT & VISUALIZATION ---
if data_source is not None:
    try:
        # Data ingestion
        df_costs = pd.read_excel(data_source, sheet_name="Custo Frete", index_col=0)
        df_data = pd.read_excel(data_source, sheet_name="Matriz de Decisões", index_col=0)

        # Optimization runs
        baseline_cost, _ = run_optimization(df_costs, df_data, 120)
        optimized_cost, df_routes = run_optimization(df_costs, df_data, cap_cd_slider)

        # Financial Calculations
        daily_savings = baseline_cost - optimized_cost
        monthly_savings = daily_savings * op_days_month
        payback_months = capex_input / monthly_savings if monthly_savings > 0 else 0

        # KPI Metrics
        st.subheader("📊 Performance Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Baseline Daily Cost", f"$ {baseline_cost:,.2f}")
        m2.metric("Optimized Daily Cost", f"$ {optimized_cost:,.2f}", delta=f"- $ {daily_savings:,.2f}", delta_color="normal")
        
        if monthly_savings > 0:
            m3.metric("Estimated Payback", f"{payback_months:.1f} Months")
        else:
            m3.metric("Estimated Payback", "N/A (No savings)")

        # Visual Analytics
        st.markdown("### Daily Cost Comparison")
        chart_df = pd.DataFrame({
            'Scenario': ['Baseline (120t)', f'Optimized ({cap_cd_slider}t)'],
            'Daily Cost ($)': [baseline_cost, optimized_cost]
        })
        st.bar_chart(data=chart_df, x='Scenario', y='Daily Cost ($)', color="#29b5e8")

        st.markdown("### Optimized Sourcing Strategy (Routes & Share)")
        st.dataframe(df_routes, use_container_width=True)

        st.success(f"💡 Operational Insight: With {op_days_month} working days, this expansion generates a monthly saving of $ {monthly_savings:,.2f}")

    except Exception as e:
        st.error(f"Execution Error: {e}")
else:
    st.warning("👈 Awaiting data input. Please provide the Excel database to proceed.")
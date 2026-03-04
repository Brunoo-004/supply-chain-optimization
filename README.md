# 🚚 Supply Chain Transformation: DC Capacity Optimization


## 📖 Executive Summary
This project addresses a strategic bottleneck in a distribution network consisting of **1 Factory, 1 Distribution Center (DC), and 5 Regional Clients**. Using **Linear Programming (GLPK Solver)**, I developed a decision-support tool to analyze the financial feasibility of expanding DC capacity. The goal is to minimize total freight costs while calculating ROI and the optimal investment point.

---

## 📊 The Logistics Scenario (Input Data)
To understand the optimization, here is the baseline operational data. The model seeks the cheapest path while respecting these demands and costs:

### 1. Daily Demand per Client
* **Client A:** 100 tons
* **Client B:** 180 tons
* **Client C:** 80 tons
* **Client D:** 120 tons
* **Client E:** 70 tons

### 2. Freight Cost Matrix ($/ton)
| From \ To | Client A | Client B | Client C | Client D | Client E |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Factory** | $35 | $60 | $20 | $65 | $115 |
| **DC (Regional)** | $25 | $20 | $60 | $20 | $50 |

> **Strategic Note:** Some DC freight rates are lower due to **Scale Economics**. Bulk transfers from the Factory to the DC are done via high-capacity trucks (lower cost per ton), while the DC handles the "Last Mile" regional delivery.

---

## 🔍 The Problem: "The Capacity Ceiling"
In the baseline scenario, the DC was capped at **120 tons/day**. 

* **The Diagnostic:** Using **Shadow Price analysis**, I identified that the DC was operating at 100% capacity, forcing the model to fulfill 70% of the total demand directly from the Factory at much higher costs.
* **The Methodology:** We analyzed **Average Daily Demand** to eliminate seasonal noise and used an **Operating Days Slider** to scale savings into a monthly financial view, providing a realistic **Payback Period**.

---

## 📈 Deep Dive: The Saturation Point
Through the **Sensitivity Analysis** included in the dashboard, we identified the "Efficiency Frontier":
1.  **The Expansion Phase:** Increasing capacity from 120t to ~300t shows a steep decline in costs.
2.  **The Saturation Point:** Beyond **320 tons**, the cost curve flattens completely.
3.  **The Insight:** At 320t, the DC can already fulfill all regional demand where it has a cost advantage. Any capacity above this would remain **idle**, leading to sub-optimal capital allocation.

---

## 📐 Final Recommendation
Based on the mathematical optimization, the strategic recommendation is:
* **Target Capacity:** **320 tons**. 
* **Investment Strategy:** This is the point of maximum efficiency. If the budget allows, expanding to 320t yields the highest ROI. Expansions beyond this point are not recommended as the marginal saving becomes zero.

---

## 🚀 Technologies Used
* **Python / Pyomo:** Optimization modeling.
* **GLPK Solver:** Linear programming engine.
* **Streamlit:** Interactive web dashboard for stakeholders.
* **Pandas / NumPy:** Data processing and sensitivity analysis.

---

### 🔗 [Live Demo: Access the Optimization Dashboard Here](https://logistics-optimizer-bruno.streamlit.app/)

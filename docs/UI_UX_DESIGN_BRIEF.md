# UI/UX Design Brief

## Employee Performance Analytics and Explainable Prediction System

**Course**: Computer Science & Engineering (3rd Year Mini Project)  
**Author**: Girish S  
**Design Target**: Desktop-First Clean & Interactive Analytics Dashboard  

---

## 1. Design Direction & Objectives

Create a modern, professional, and easy-to-use workforce analytics dashboard that helps users explore employee data, understand performance patterns, and view explainable machine-learning predictions.

* **Visual Analytics**: Make employee data clear and intuitive through interactive Plotly visualisations.
* **Simple Navigation**: Provide persistent sidebar navigation between all 7 core pages.
* **Explainable Outputs**: Present performance estimations and local factor contributions transparently.
* **Clear Hierarchy**: Place high-level KPI metric cards at the top, followed by charts, and detailed data tables below.

---

## 2. Visual Design System

### Color Palette

| Color Name | Hex Code | Purpose / Usage |
|---|---|---|
| **Navy Blue** | `#0F172A` / `#172B4D` | Primary sidebar navigation, headers, dark backgrounds |
| **Primary Blue** | `#2563EB` | Active navigation states, primary action buttons |
| **Teal / Emerald** | `#14B8A6` / `#10B981` | Highlights, positive drivers, 'High' category badges |
| **Amber Gold** | `#F59E0B` | 'Moderate' category badges, warning alerts |
| **Crimson Red** | `#EF4444` | 'Needs Support' category badges, negative drivers |
| **Slate Grey** | `#1E293B` / `#334155` | Card panels, table headers, border lines |

### Typography & Components
* **Headings**: `Poppins`, `Inter` (Semibold, 600-700 weight).
* **Body Text**: `Inter`, `Roboto` (Regular, 400 weight).
* **Metrics**: Large bold typography (`2.1rem` size).
* **Cards**: 14px rounded corners (`border-radius: 14px`) with subtle hover shadow.

---

## 3. UI Interaction States

| Interaction State | Behavior & Visual Indicator |
|---|---|
| **Default State** | Displays 600 synthetic employee records with full analytics. |
| **Empty State** | Displays clear upload instructions when no custom dataset is loaded. |
| **Loading State** | Progress indicator / spinner during model fitting and prediction execution. |
| **Success State** | Green toast/badge confirming dataset validation or model training completion. |
| **Error State** | Informative warning box explaining input/format errors and resolution steps. |
| **Prediction State** | Displays predicted performance category badge, probability gauge, waterfall chart, and caveat disclaimer. |
| **Export State** | Download confirmation for CSV export and Markdown project reports. |

---

## 4. UX Principles

1. **Persistent Navigation**: Keep all 7 main sections accessible from the navy sidebar.
2. **Visual Hierarchy**: Display top-level summary KPIs first, followed by analytical charts, and detailed data tables.
3. **Consistent Component Styling**: Use identical color tokens, border radiuses, and button states across all pages.
4. **Responsible Predictions**: Frame output labels non-judgmentally (`High Performance`, `Moderate Performance`, `Needs Support`).

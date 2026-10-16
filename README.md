# Social Network Analysis

A Python and Streamlit web application for analyzing and visualizing social network graphs.

## Prerequisites

- Python 3.9+ installed on Windows

## Setup (Windows)

1. **Create and activate a virtual environment (recommended):**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   *(For Command Prompt: `venv\Scripts\activate.bat`)*

2. **Install dependencies:**
   ```powershell
   python -m pip install -r requirements.txt
   ```

## Running the Application

Start the Streamlit application:
```powershell
python -m streamlit run app.py
```
*(Or if your environment PATH is configured: `streamlit run app.py`)*

## Features

- **Dashboard Overview**: Real-time KPI metrics, most-connected members, and degree distribution table.
- **Manage Network**: Interactive forms to add and remove individuals and friendships with instant validation.
- **Friend Analysis**: Pairwise connection comparison, direct status, and mutual friends using set intersection.
- **Graph Analysis**: Shortest path navigation using Breadth-First Search (BFS), cycle detection, connected components, and isolated node detection.
- **Network Statistics & Visualization**: Interactive network topology graph rendered with Matplotlib (highlighting most-connected members and isolated individuals), density metrics, and binary adjacency matrix.
- **Persistent Storage**: Changes are automatically saved to `social_network.json`.

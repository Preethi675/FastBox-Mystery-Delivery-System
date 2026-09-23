
# FastBox Mystery Delivery System — Web Edition

A localhost web application for the Mystery Delivery System assignment.

## Features
- Professional FastBox logistics dashboard
- HTML/CSS responsive UI
- Python Flask backend
- Select any JSON test case
- Upload your own JSON case
- Nearest-agent assignment
- Euclidean distance calculation
- Agent → Warehouse → Destination simulation
- Live-style delivery event feed
- Agent performance table
- Package assignment table
- Route operation view
- JSON report download
- Top performer CSV export
- Supports both common input shapes:
  - `"warehouses": [{"id":"W1","location":[0,0]}]`
  - `"warehouses": {"W1":[0,0]}`

## Folder structure

FastBox_Mystery_Delivery_Web/
├── app.py
├── requirements.txt
├── README.md
├── cases/
├── outputs/
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── app.js

## Run on Windows

1. Extract the ZIP.
2. Open the extracted folder in VS Code.
3. Open Terminal.
4. Create a virtual environment:

   python -m venv venv

5. Activate it:

   venv\Scripts\activate

6. Install Flask:

   pip install -r requirements.txt

7. Start the website:

   python app.py

8. Open in browser:

   http://127.0.0.1:5000

## How to use

1. Select a test case from the CASE dropdown.
2. Click **Run Simulation**.
3. Dashboard shows package count, delivered count, agents and total distance.
4. Open **Operations** for every route event.
5. Open **Agents** for performance.
6. Open **Packages** for assignment status.
7. Open **Reports** to download report.json or top_performer.csv.
8. Use **Upload JSON** to test another case.

## Important

This is a local web simulation, not a GPS/live-map production system. The assignment JSON contains coordinates, so the application simulates delivery movement using those coordinates.

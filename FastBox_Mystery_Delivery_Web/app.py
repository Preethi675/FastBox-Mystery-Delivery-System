
from flask import Flask, render_template, request, jsonify, send_file
from pathlib import Path
import json, math, csv, io, time, uuid

BASE_DIR = Path(__file__).resolve().parent
CASES_DIR = BASE_DIR / "cases"
OUTPUT_DIR = BASE_DIR / "outputs"
CASES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

app = Flask(__name__)

def distance(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])

def normalize_entities(raw, key):
    value = raw.get(key, [])
    result = {}
    if isinstance(value, dict):
        for ident, loc in value.items():
            result[str(ident)] = {"id": str(ident), "location": [float(loc[0]), float(loc[1])]}
    elif isinstance(value, list):
        for item in value:
            ident = item.get("id") or item.get("agent_id") or item.get("warehouse_id")
            loc = item.get("location") or item.get("coordinates") or item.get("position")
            if ident is not None and loc is not None:
                result[str(ident)] = {"id": str(ident), "location": [float(loc[0]), float(loc[1])]}
    return result

def load_case(path):
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    warehouses = normalize_entities(raw, "warehouses")
    agents = normalize_entities(raw, "agents")
    packages_raw = raw.get("packages", [])
    packages = []
    for p in packages_raw:
        pid = str(p.get("id") or p.get("package_id"))
        wid = str(p.get("warehouse") or p.get("warehouse_id"))
        dest = p.get("destination") or p.get("destination_location")
        if not pid or wid not in warehouses or not dest:
            continue
        packages.append({
            "id": pid, "warehouse": wid,
            "destination": [float(dest[0]), float(dest[1])]
        })
    return {"warehouses": warehouses, "agents": agents, "packages": packages}

def simulate(case, delay=0):
    warehouses = case["warehouses"]
    agents = {
        aid: {
            "id": aid, "start": list(a["location"]),
            "location": list(a["location"]), "packages": [],
            "total_distance": 0.0, "events": []
        }
        for aid, a in case["agents"].items()
    }
    assignments = {}
    for p in case["packages"]:
        wh = warehouses[p["warehouse"]]["location"]
        chosen = min(
            agents.values(),
            key=lambda a: (distance(a["location"], wh), a["id"])
        )
        # Assignment is based on the agent's current location, making the
        # web simulation more realistic while remaining deterministic.
        assignments[p["id"]] = chosen["id"]
        chosen["packages"].append(p["id"])

    events = []
    sequence = 0
    for p in case["packages"]:
        aid = assignments[p["id"]]
        a = agents[aid]
        wh = warehouses[p["warehouse"]]["location"]
        start = list(a["location"])
        to_wh = distance(start, wh)
        delivery = distance(wh, p["destination"])
        total = to_wh + delivery
        a["total_distance"] += total
        a["location"] = list(p["destination"])
        sequence += 1
        event = {
            "sequence": sequence, "agent_id": aid, "package_id": p["id"],
            "warehouse_id": p["warehouse"], "start": start,
            "warehouse": list(wh), "destination": list(p["destination"]),
            "to_warehouse_distance": round(to_wh, 2),
            "delivery_distance": round(delivery, 2),
            "package_distance": round(total, 2),
            "cumulative_distance": round(a["total_distance"], 2),
            "status": "DELIVERED"
        }
        events.append(event)
        a["events"].append(event)

    report_agents = []
    for a in agents.values():
        count = len(a["packages"])
        report_agents.append({
            "id": a["id"],
            "packages_delivered": count,
            "total_distance": round(a["total_distance"], 2),
            "efficiency": round(a["total_distance"] / count, 2) if count else 0,
            "package_ids": a["packages"],
            "final_location": a["location"]
        })
    active = [a for a in report_agents if a["packages_delivered"]]
    best = min(active, key=lambda a: (a["efficiency"], a["id"]))["id"] if active else None
    return {
        "summary": {
            "warehouses": len(warehouses), "agents": len(agents),
            "packages": len(case["packages"]),
            "delivered": len(events),
            "total_distance": round(sum(a["total_distance"] for a in agents.values()), 2)
        },
        "agents": report_agents,
        "best_agent": best,
        "assignments": assignments,
        "events": events
    }

def case_names():
    return sorted([p.name for p in CASES_DIR.glob("*.json")])

def get_case_path(name):
    safe = Path(name).name
    path = CASES_DIR / safe
    if not path.exists():
        raise FileNotFoundError(safe)
    return path

# Seed bundled case files from project root.
for src in BASE_DIR.glob("*_case.json"):
    dest = CASES_DIR / src.name
    if not dest.exists():
        shutil.copy2(src, dest)
for src in BASE_DIR.glob("test_case_*.json"):
    dest = CASES_DIR / src.name
    if not dest.exists():
        shutil.copy2(src, dest)

@app.route("/")
def index():
    return render_template("index.html", cases=case_names())

@app.get("/api/cases")
def api_cases():
    return jsonify({"cases": case_names()})

@app.get("/api/case/<path:name>")
def api_case(name):
    try:
        case = load_case(get_case_path(name))
        return jsonify({
            "name": Path(name).name,
            "warehouses": list(case["warehouses"].values()),
            "agents": list(case["agents"].values()),
            "packages": case["packages"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.post("/api/upload")
def api_upload():
    f = request.files.get("file")
    if not f or not f.filename.lower().endswith(".json"):
        return jsonify({"error": "Please upload a JSON case file."}), 400
    name = Path(f.filename).name
    target = CASES_DIR / name
    f.save(target)
    # Validate immediately.
    try:
        case = load_case(target)
        return jsonify({"ok": True, "name": name, "counts": {
            "warehouses": len(case["warehouses"]),
            "agents": len(case["agents"]),
            "packages": len(case["packages"])
        }})
    except Exception as e:
        target.unlink(missing_ok=True)
        return jsonify({"error": f"Invalid case JSON: {e}"}), 400

@app.post("/api/simulate")
def api_simulate():
    data = request.get_json(silent=True) or {}
    try:
        case = load_case(get_case_path(data.get("case", "base_case.json")))
        report = simulate(case)
        report["case_name"] = Path(data.get("case", "base_case.json")).name
        (OUTPUT_DIR / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.get("/api/report.json")
def download_json():
    path = OUTPUT_DIR / "report.json"
    if not path.exists():
        return jsonify({"error": "Run a simulation first."}), 404
    return send_file(path, as_attachment=True, download_name="report.json")

@app.get("/api/top_performer.csv")
def download_csv():
    path = OUTPUT_DIR / "top_performer.csv"
    report_path = OUTPUT_DIR / "report.json"
    if not report_path.exists():
        return jsonify({"error": "Run a simulation first."}), 404
    report = json.loads(report_path.read_text(encoding="utf-8"))
    best = report.get("best_agent")
    agent = next((a for a in report["agents"] if a["id"] == best), None)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["agent_id", "packages_delivered", "total_distance", "efficiency"])
    if agent:
        writer.writerow([agent["id"], agent["packages_delivered"], agent["total_distance"], agent["efficiency"]])
    path.write_text(output.getvalue(), encoding="utf-8")
    return send_file(path, as_attachment=True, download_name="top_performer.csv")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

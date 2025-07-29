import os
import json
import requests
from datetime import datetime
from pathlib import Path
from jinja2 import Template
from .config import get_api_key

API_KEY = get_api_key()
RESULT_DIR = Path.home() / "Mal_Detector_result"
RESULT_DIR.mkdir(parents=True, exist_ok=True)

VT_HEADERS = {"x-apikey": API_KEY}
VT_URL = "https://www.virustotal.com/api/v3"

def scan_url(url):
    response = requests.post(f"{VT_URL}/urls", headers=VT_HEADERS, data={"url": url})
    response.raise_for_status()
    analysis_id = response.json()["data"]["id"]
    analysis = requests.get(f"{VT_URL}/analyses/{analysis_id}", headers=VT_HEADERS)
    return analysis.json()

def scan_file(file_path):
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        response = requests.post(f"{VT_URL}/files", headers=VT_HEADERS, files=files)
        response.raise_for_status()
        analysis_id = response.json()["data"]["id"]
        analysis = requests.get(f"{VT_URL}/analyses/{analysis_id}", headers=VT_HEADERS)
        return analysis.json()

def sanitize_filename(name):
    return "".join(c if c.isalnum() else "_" for c in name)[:50]

def save_result_as_html(result: dict, name_hint: str):
    sanitized_name = sanitize_filename(name_hint)
    file_name = f"scan_{sanitized_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    file_path = RESULT_DIR / file_name

    stats = result.get("data", {}).get("attributes", {}).get("results", {})

    html_template = Template("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>VT Scan Result - {{ name }}</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background-color: #f0f4f8;
            color: #333;
            padding: 20px;
        }
        h1 {
            color: #007BFF;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: #fff;
            box-shadow: 0 0 10px rgba(0,0,0,0.05);
        }
        th, td {
            padding: 12px 15px;
            border: 1px solid #e3e6f0;
            text-align: left;
        }
        th {
            background-color: #007BFF;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f9fbfd;
        }
        pre {
            background: #eef;
            padding: 15px;
            border-left: 4px solid #007BFF;
            overflow-x: auto;
        }
    </style>
</head>
<body>
    <h1>VirusTotal Scan Result</h1>
    <h2>Target: {{ name }}</h2>
    <table>
        <tr>
            <th>Engine</th>
            <th>Category</th>
            <th>Result</th>
        </tr>
        {% for engine, details in stats.items() %}
        <tr>
            <td>{{ engine }}</td>
            <td>{{ details.category }}</td>
            <td>{{ details.result if details.result else "Clean" }}</td>
        </tr>
        {% endfor %}
    </table>

  
</body>
</html>""")

    rendered = html_template.render(name=name_hint, stats=stats, full_json=json.dumps(result, indent=2))
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(rendered)

    return str(file_path)
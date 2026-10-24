from datetime import datetime
import json
import math
import requests
from flask import Flask, jsonify, request, render_template
from gemma_integration import ask_gemma  # Teammate's original function!

app = Flask(__name__, template_folder='.')

# -------------------------------------------------------------
# HELPER FUNCTIONS & MATH ENGINE
# -------------------------------------------------------------

def parse_time_to_minutes(time_str):
    """Parses time strings like '07:00 PM' into minutes from midnight for chronological sorting."""
    try:
        clean_time = str(time_str).strip().upper()
        dt = datetime.strptime(clean_time, "%I:%M %p")
        return dt.hour * 60 + dt.minute
    except ValueError:
        try:
            dt = datetime.strptime(clean_time, "%H:%M")
            return dt.hour * 60 + dt.minute
        except ValueError:
            return 23 * 60 + 59  # Default to end of day on parse failure


def sort_itinerary_chronologically(itinerary_matrix):
    """Sorts spreadsheet rows chronologically from morning to night."""
    return sorted(itinerary_matrix, key=lambda row: parse_time_to_minutes(row.get("time", "11:59 PM")))


def calculate_distance_km(lat1, lon1, lat2, lon2):
    """Calculates straight-line distance in kilometers between two coordinates."""
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_real_coordinates(place_name, address):
    """
    GEOCODING VERIFICATION:
    Queries OpenStreetMap (Nominatim) using fallback strategies to replace hallucinated 
    coordinates with real physical lat/lng values.
    """
    headers = {'User-Agent': 'SheetMapHackathonApp/1.0'}
    
    # Strategy 1: Search by Name + Address
    try:
        query = f"{place_name}, {address}"
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.quote(query)}"
        res = requests.get(url, headers=headers, timeout=3).json()
        if res:
            return float(res[0]['lat']), float(res[0]['lon'])
    except Exception:
        pass

    # Strategy 2: Search by Name + City
    try:
        query = f"{place_name}, London"
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.quote(query)}"
        res = requests.get(url, headers=headers, timeout=3).json()
        if res:
            return float(res[0]['lat']), float(res[0]['lon'])
    except Exception:
        pass

    # Strategy 3: Fall back to searching address landmark
    try:
        query = f"{address}"
        url = f"https://nominatim.openstreetmap.org/search?format=json&q={requests.utils.quote(query)}"
        res = requests.get(url, headers=headers, timeout=3).json()
        if res:
            return float(res[0]['lat']), float(res[0]['lon'])
    except Exception:
        pass

    return None, None


def get_place_from_gemma(user_prompt):
    """Formats the strict spatial system prompt, calls ask_gemma(), and verifies map coordinates."""
    formatted_prompt = f"""
    You are an expert travel planner and spatial routing assistant.
    Find a REAL, existing physical business matching the user request.
    
    STRICT SPATIAL CONSTRAINT:
    If the user mentions a landmark (e.g. Big Ben, London Eye), the venue MUST be within a strict 10-minute walk (under 1 km / 0.6 miles) of that landmark.
    Do NOT suggest venues in far neighborhoods (e.g. Covent Garden or Soho if Big Ben was asked).
    
    Respond ONLY with valid JSON with NO markdown formatting:
    {{
        "name": "REAL Venue Name",
        "category": "Dining/Lunch/Activity",
        "time": "07:00 PM",
        "estimated_cost": 45.0,
        "address": "Full real street address, City",
        "lat": 51.5132,
        "lng": -0.1558
    }}

    User Request: {user_prompt}
    """
    raw_response = ask_gemma(formatted_prompt)

    try:
        cleaned_text = raw_response.replace("```json", "").replace("```", "").strip()
        place_data = json.loads(cleaned_text)
    except Exception as e:
        print(f"⚠️ JSON Parsing fallback triggered: {e}")
        place_data = {
            "name": "The Cinnamon Club",
            "category": "Dining",
            "time": "08:00 PM",
            "estimated_cost": 38.0,
            "address": "The Old Westminster Library, 30 Great Smith St, London SW1P 3BU",
            "lat": 51.4979,
            "lng": -0.1299
        }

    # Cross-reference coordinates with OpenStreetMap
    real_lat, real_lng = get_real_coordinates(place_data.get("name", ""), place_data.get("address", ""))
    if real_lat is not None and real_lng is not None:
        place_data["lat"] = real_lat
        place_data["lng"] = real_lng

    return place_data


# -------------------------------------------------------------
# FLASK API ROUTES
# -------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add-item", methods=["POST"])
def add_item():
    payload = request.get_json(force=True) or {}
    user_prompt = payload.get("prompt", "")
    existing_matrix = payload.get("current_matrix", [])

    if not user_prompt:
        return jsonify({"error": "Prompt is required"}), 400

    # 1. AI Location Parse & Geocoding Check
    new_place_data = get_place_from_gemma(user_prompt)

    # 2. Append to spreadsheet matrix
    updated_matrix = list(existing_matrix)
    updated_matrix.append(new_place_data)

    # 3. Chronological Sorting Engine (Morning -> Night)
    sorted_matrix = sort_itinerary_chronologically(updated_matrix)

    # 4. Spatial Routing Engine (Calculate distance & flag long travel jumps)
    for i in range(len(sorted_matrix) - 1):
        curr_item = sorted_matrix[i]
        next_item = sorted_matrix[i + 1]
        
        dist = calculate_distance_km(
            curr_item.get("lat", 0), curr_item.get("lng", 0),
            next_item.get("lat", 0), next_item.get("lng", 0)
        )
        
        # Flag if distance between consecutive steps exceeds 1.5 km (~15 min travel)
        if dist > 1.5:
            next_item["travel_warning"] = f"🚶 ~{int(dist * 12)} min travel from {curr_item['name']}"
        else:
            next_item["travel_warning"] = None

    # 5. Live Budget Calculator
    total_budget = sum(float(item.get("estimated_cost", 0)) for item in sorted_matrix)

    return jsonify({
        "success": True,
        "master_matrix": sorted_matrix,
        "total_budget": total_budget,
        "added_item": new_place_data
    })


if __name__ == "__main__":
    print("🚀 SheetMap Logic Engine running at http://127.0.0.1:5000", flush=True)
    app.run(host="127.0.0.1", port=5000, debug=True)
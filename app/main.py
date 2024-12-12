from flask import Flask, request, jsonify
from google.cloud import firestore
from datetime import datetime
import os
from .cbf import recommend
from .tsp import solve_tsp

# Inisialisasi Firestore
firestore_client = firestore.Client()

# Inisialisasi Flask
app = Flask(__name__)

# Fungsi bantu menghitung durasi
def calculate_duration(start_date, end_date):
    start = datetime.strptime(start_date, "%d-%m-%Y")
    end = datetime.strptime(end_date, "%d-%m-%Y")
    return (end - start).days + 1

# Endpoint rekomendasi
@app.route('/recommend', methods=['POST'])
def recommend_places():
    data = request.get_json()
    city = data.get("city")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    price_category = data.get("price_category")

    if not all([city, start_date, end_date, price_category]):
        return jsonify({"error": "Missing required fields"}), 400

    num_days = calculate_duration(start_date, end_date)
    recommendations_per_slot = {
        slot: recommend(city, price_category, slot, top_n=3)
        for slot in ['morning', 'afternoon', 'evening']
    }

    selected_places = []
    for day in range(num_days):
        day_places = {}
        for slot, rec in recommendations_per_slot.items():
            if not rec.empty:
                selected_place = rec.iloc[0]
                day_places[slot] = selected_place.to_dict()
                recommendations_per_slot[slot] = rec.iloc[1:]
        selected_places.append({"day": f"Day {day + 1}", "places": day_places})

    optimized_routes = []
    for day_index, day_info in enumerate(selected_places):
        places_with_coords = {
            place['Place_Name']: (float(place['Lat']), float(place['Long']))
            for place in day_info["places"].values()
        }
        route_info = solve_tsp(places_with_coords)
        if route_info:
            optimized_routes.append({
                "day": f"Day {day_index + 1}",
                "route": route_info["route"],
                "total_distance": route_info["total_distance"]
            })

    # Simpan data ke Firestore
    doc_ref = db.collection('Recommendations').document()
    doc_ref.set({
        "city": city,
        "start_date": start_date,
        "end_date": end_date,
        "price_category": price_category,
        "selected_places": selected_places,
        "routes": optimized_routes
    })

    return jsonify({
        "selected_places": selected_places,
        "routes": optimized_routes
    })

# Endpoint optimasi rute
@app.route('/optimize_route', methods=['POST'])
def get_optimized_route():
    data = request.json
    places_with_coords = data.get('places')

    if not places_with_coords:
        return jsonify({'error': 'No places provided for optimization'}), 400

    result = solve_tsp(places_with_coords)
    if result:
        return jsonify(result)
    else:
        return jsonify({'error': 'Could not optimize the route'}), 500

if __name__ == '__main__':
    # Gunakan PORT dari environment atau default ke 8080
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

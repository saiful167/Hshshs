import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# কনফিগারেশন
API_KEY = "r3f6PifXWq7w6XLjXJVHFKgMCngyieVW8sySBB38O7"
EXTRACT_API_URL = "https://api.extract.pics/v0/extractions"


def filter_magnific_images(data):
    """বিশাল JSON থেকে শুধু দরকারি লিঙ্কগুলো ছেঁটে ছোট করে ফেলে"""
    if not data or "data" not in data:
        return data

    original_images = data["data"].get("images", [])
    filtered_list = []

    for img in original_images:
        url = img.get("url", "")
        # শুধুমাত্র Magnific এর অরিজিনাল বড় ছবিগুলো নেওয়া হচ্ছে
        if "img.magnific.com/premium-photo/" in url and "?w=" not in url:
            if url not in filtered_list:
                filtered_list.append(url)

    # সর্বোচ্চ ১৫টি ছবি পাঠাবে
    return {
        "id": data["data"].get("id"),
        "status": data["data"].get("status"),
        "images": filtered_list[:15]
    }


@app.route('/api/extract', methods=['POST'])
def start_extraction():
    """URL দিয়ে extraction শুরু করো, ID ফেরত পাবে"""
    body = request.get_json()
    if not body:
        return jsonify({"error": "JSON body required"}), 400

    url = body.get("url")
    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        res = requests.post(
            EXTRACT_API_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={"url": url},
            timeout=30
        )
        return jsonify(res.json()), res.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/extract', methods=['GET'])
def get_result():
    """ID দিয়ে ছবির লিঙ্ক আনো"""
    ext_id = request.args.get("id")
    if not ext_id:
        return jsonify({"error": "Extraction ID is required"}), 400

    try:
        res = requests.get(
            f"{EXTRACT_API_URL}/{ext_id}",
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30
        )

        raw_data = res.json()

        # যদি এক্সট্রাকশন শেষ হয়, তবে ডাটা ফিল্টার করো
        if res.status_code == 200 and raw_data.get("data", {}).get("status") == "done":
            optimized_data = filter_magnific_images(raw_data)
            return jsonify(optimized_data), 200

        return jsonify(raw_data), res.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "Magnific Proxy API is Running!",
        "endpoints": {
            "POST /api/extract": "URL দিয়ে extraction শুরু করো",
            "GET /api/extract?id=XXX": "ID দিয়ে ছবির লিঙ্ক আনো"
        }
    })

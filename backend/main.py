from flask import Flask, request, jsonify
from algorithms.fifo import fifo
from algorithms.lru import lru
from algorithms.optimal import optimal
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


ALGO_MAP ={
    "FIFO": fifo,
    "LRU": lru,
    "OPTIMAL": optimal
}

@app.route("/api/run", methods=["POST"])

def run_algorithms():
    data = request.get_json()

    process_id = data.get("processId")
    memory_size = data.get("memorySize")
    reference_string = data.get("referenceString")
    frames = data.get("frames")
    algorithms = data.get("algorithms")  # list of algorithm names

    results = {}

    for algo_name in algorithms:
        func = ALGO_MAP.get(algo_name.upper())
        if func:
            result = func(process_id, memory_size, reference_string, frames)
            results[algo_name.upper()] = result
        else:
            results[algo_name.upper()] = {"error": "Algorithm not found"}

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000,debug=True)




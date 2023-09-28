from flask import Flask, request, jsonify

app = Flask(__name__)

# List to store all transactions
transactions = []

# Dictionary to store the current balance of each payer
points = {}

# Tracks when negative points are added
negative_points = {}

# Used to track which transactions we've spent points from
# without altering transaction history
current_transaction = 0
points_holdover = 0
payer_holdover = ""


# Helper function to add a transaction.
def add_transaction(payer, points_value, timestamp):
    if payer not in points:
        points[payer] = points_value
    else:
        points[payer] += points_value

    if points[payer] < 0:
        points[payer] = 0

    if points_value < 0:
        if payer not in negative_points:
            negative_points[payer] = points_value
        else:
            negative_points[payer] += points_value

    transactions.append({
        "payer": payer,
        "points": points_value,
        "timestamp": timestamp
    })
    transactions.sort(key=lambda data: data['timestamp'])

#Helper function to handle holdover logic
def holdover(points_to_spend):
    global current_transaction, points_holdover, payer_holdover
    spent_points = []

    deduct = min(points_holdover, points_to_spend)

    spent_points.append({"payer": payer_holdover, "points": -deduct})

    points[payer_holdover] -= deduct
    points_to_spend -= deduct
    points_holdover -= deduct

    if points[payer_holdover] < 0: 
        points[payer_holdover] = 0 
    
    if points_holdover == 0:
        current_transaction += 1
    
    return spent_points

# Helper function to spend points.
def spend_points(points_to_spend):
    global points_holdover, payer_holdover, current_transaction

    spent_points = []

    while current_transaction < len(transactions) and points_to_spend > 0:
        t_payer = transactions[current_transaction]["payer"]
        t_points = transactions[current_transaction]["points"]

        # If there is a holdover from the last transaction
        if points_holdover > 0:
            spent_points = holdover(points_to_spend)

            if points_holdover == 0: 
                current_transaction = current_transaction + 1

        # If the current transaction has positive points
        elif t_points > 0:

            # If there are negative points that were added, subtract this from current
            # transactions alotted points (not altering historical data)
            if t_payer in negative_points and negative_points[t_payer] < 0:
                negation = min(-negative_points[t_payer], t_points)
                t_points = transactions[current_transaction]["points"] - negation
                negative_points[t_payer] += negation

            # Use up points allotted by current transaction, otherwise roll-over extra points
            if t_points <= points_to_spend:
                spent_points.append({"payer": t_payer, "points": -t_points})
                points[t_payer] -= t_points
                points_to_spend -= t_points
                current_transaction += 1
            else:
                spent_points.append(
                    {"payer": t_payer, "points": -points_to_spend})
                points[t_payer] -= points_to_spend
                points_holdover = t_points - points_to_spend
                payer_holdover = t_payer
                points_to_spend = 0

            if points[t_payer] < 0: 
                points[t_payer] = 0 
        # If the current transaction has negative points, skip it
        else:
            current_transaction += 1

    # Aggregate the spent points by payer
    result = {}
    for entry in spent_points:
        payer = entry["payer"]
        if payer in result:
            result[payer] += entry["points"]
        else:
            result[payer] = entry["points"]

    return result

# Endpoint to add a transaction.
@app.route("/add", methods=["POST"])
def add():
    data = request.get_json()
    required_keys = {'payer', 'points', 'timestamp'}

    if not required_keys.issubset(data.keys()):
        return jsonify({"error": "Required field missing"}), 400

    add_transaction(data["payer"], data["points"], data["timestamp"])

    return '', 200

# Endpoint to spend points.
@app.route("/spend", methods=["POST"])
def spend():
    # Parse the JSON data from the request
    data = request.get_json()

    # Check if 'points' key exists in the request data
    if "points" not in data:
        return "Missing points in request.", 400

    points_to_spend = data["points"]

    # Check if there are enough points to spend
    if points_to_spend > sum(points.values()):
        return "Not enough points.", 400

    result = spend_points(points_to_spend)

    return jsonify([{"payer": k, "points": v} for k, v in result.items()]), 200

# Endpoint to get the current balance of each payer.
@app.route("/balance", methods=["GET"])
def balance():
    return jsonify(points), 200

# Endpoint to reset transaction tracking data. Added for testing purposes.
@app.route("/reset", methods=["POST"])
def reset():
    global current_transaction, payer_holdover, points_holdover

    current_transaction = 0
    points_holdover = 0
    payer_holdover = ""

    return jsonify({"message": "State reset successfully!"}), 200

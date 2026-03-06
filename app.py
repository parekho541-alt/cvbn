from flask import Flask, render_template, request, jsonify
import sqlite3
import os
from database import get_db_connection, init_bids_table

app = Flask(__name__)

# Ensure database is ready
init_bids_table()

def get_highest_bid_data(player_id):
    conn = get_db_connection()
    bid = conn.execute(
        "SELECT bid_amount, bidder_name FROM bids WHERE player_id = ? ORDER BY bid_amount DESC LIMIT 1", 
        (player_id,)
    ).fetchone()
    conn.close()
    if bid:
        return {"amount": bid["bid_amount"], "bidder": bid["bidder_name"]}
    # If no bids exist, return base price (10,000)
    return {"amount": 10000, "bidder": "Starting Price"}

@app.route('/')
def index():
    conn = get_db_connection()
    players = conn.execute("SELECT * FROM players").fetchall()
    
    players_list = []
    for p in players:
        p_dict = dict(p)
        bid_info = get_highest_bid_data(p_dict['id'])
        p_dict['current_bid'] = bid_info['amount']
        p_dict['highest_bidder'] = bid_info['bidder']
        players_list.append(p_dict)
    
    conn.close()
    return render_template('index.html', players=players_list)

@app.route('/player/<int:player_id>')
def player_profile(player_id):
    conn = get_db_connection()
    player = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    conn.close()
    
    if not player:
        return "Player not found", 404
        
    p_dict = dict(player)
    bid_info = get_highest_bid_data(player_id)
    p_dict['current_bid'] = bid_info['amount']
    p_dict['highest_bidder'] = bid_info['bidder']
    
    return render_template('player.html', player=p_dict)

@app.route('/api/players')
def get_players_api():
    conn = get_db_connection()
    players = conn.execute("SELECT * FROM players").fetchall()
    
    players_list = []
    for p in players:
        p_dict = dict(p)
        bid_info = get_highest_bid_data(p_dict['id'])
        p_dict['current_bid'] = bid_info['amount']
        p_dict['highest_bidder'] = bid_info['bidder']
        players_list.append(p_dict)
    
    conn.close()
    return jsonify(players_list)

@app.route('/api/player/<int:player_id>')
def get_player_api(player_id):
    conn = get_db_connection()
    player = conn.execute("SELECT * FROM players WHERE id = ?", (player_id,)).fetchone()
    conn.close()
    
    if not player:
        return jsonify({"error": "Player not found"}), 404
        
    p_dict = dict(player)
    bid_info = get_highest_bid_data(player_id)
    p_dict['current_bid'] = bid_info['amount']
    p_dict['highest_bidder'] = bid_info['bidder']
    
    return jsonify(p_dict)

@app.route('/bid', methods=['POST'])
def place_bid():
    data = request.json
    player_id = data.get('player_id')
    bidder_name = data.get('bidder_name')
    bid_amount = data.get('bid_amount')
    
    if not all([player_id, bidder_name, bid_amount]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400
    
    try:
        bid_amount = int(bid_amount)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid bid amount"}), 400

    current_bid_info = get_highest_bid_data(player_id)
    
    if bid_amount <= current_bid_info['amount']:
        return jsonify({"success": False, "message": "Bid must be higher than the current bid."}), 400
        
    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO bids (player_id, bid_amount, bidder_name) VALUES (?, ?, ?)",
            (player_id, bid_amount, bidder_name)
        )
        conn.commit()
        return jsonify({"success": True, "message": "Bid placed successfully!"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)

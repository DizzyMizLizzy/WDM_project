import os
import atexit
import uuid
import requests
from flask import Flask, jsonify
import redis

app = Flask("order-service")

db: redis.Redis = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ["REDIS_PORT"]),
    password=os.environ["REDIS_PASSWORD"],
    db=int(os.environ["REDIS_DB"]),
)

gateway_url = os.environ["GATEWAY_URL"]


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


def get_item_price(item_id):
    response = requests.get(f"{gateway_url}/stock/find/{item_id}")
    if response.status_code == 200:
        return response.json()["price"]
    else:
        return None


def subtract_stock_quantity(item_id, quantity):
    response = requests.post(f"{gateway_url}/stock/subtract/{item_id}/{quantity}")
    return response.status_code == 200


def add_stock_quantity(item_id, quantity):
    response = requests.post(f"{gateway_url}/stock/add/{item_id}/{quantity}")
    return response.status_code == 200


@app.post("/create/<user_id>")
def create_order(user_id):
    order_id = str(uuid.uuid4())
    order_data = {
        "order_id": order_id,
        "paid": "False",
        "items": "[]",
        "user_id": user_id,
        "total_cost": 0,
    }
    db.hmset(f"order:{order_id}", order_data)
    return jsonify({"order_id": order_id}), 200


@app.delete("/remove/<order_id>")
def remove_order(order_id):
    db.delete(f"order:{order_id}")
    return jsonify({"status": "success"}), 200


@app.post("/addItem/<order_id>/<item_id>")
def add_item(order_id, item_id):
    order_key = f"order:{order_id}"
    order_data = db.hgetall(order_key)
    if not order_data:
        return jsonify({"error": "Order not found"}), 400

    item_price = get_item_price(item_id)
    if item_price is None:
        return jsonify({"error": "Item not found"}), 400

    if not subtract_stock_quantity(item_id, 1):
        return jsonify({"error": "Not enough stock"}), 400

    items = eval(order_data[b"items"].decode())
    items.append(item_id)
    total_cost = int(order_data[b"total_cost"]) + item_price
    db.hmset(order_key, {"items": str(items), "total_cost": total_cost})
    return jsonify({"status": "success"}), 200


@app.delete("/removeItem/<order_id>/<item_id>")
def remove_item(order_id, item_id):
    order_key = f"order:{order_id}"
    order_data = db.hgetall(order_key)
    if not order_data:
        return jsonify({"error": "Order not found"}), 400

    item_price = get_item_price(item_id)
    if item_price is None:
        return jsonify({"error": "Item not found"}), 400

    items = eval(order_data[b"items"].decode())
    if item_id not in items:
        return jsonify({"error": "Item not in order"}), 400

    items.remove(item_id)
    total_cost = int(order_data[b"total_cost"]) - item_price
    add_stock_quantity(item_id, 1)
    db.hmset(order_key, {"items": str(items), "total_cost": total_cost})
    return jsonify({"status": "success"}), 200


@app.get("/find/<order_id>")
def find_order(order_id):
    order_key = f"order:{order_id}"
    order_data = db.hgetall(order_key)
    if not order_data:
        return jsonify({"error": "Order not found"}), 400
    order = {
        key.decode(): (value.decode() if key != b"items" else eval(value.decode()))
        for key, value in order_data.items()
    }

    return jsonify(order), 200


@app.post("/checkout/<order_id>")
def checkout(order_id):
    order_key = f"order:{order_id}"
    order_data = db.hgetall(order_key)
    if not order_data:
        return jsonify({"error": "Order not found"}), 400
    user_id = order_data[b"user_id"].decode()
    total_cost = int(order_data[b"total_cost"])
    payment_response = requests.post(
        f"{gateway_url}/payment/pay/{user_id}/{order_id}/{total_cost}"
    )

    if payment_response.status_code == 200:
        items = eval(order_data[b"items"].decode())
        for item_id in items:
            subtract_stock_quantity(item_id, 1)
        db.hmset(order_key, {"items": str(items), "paid": "True"})
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Payment failed"}), 400

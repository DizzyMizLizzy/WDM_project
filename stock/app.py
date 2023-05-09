import os
import atexit
from flask import Flask, jsonify
import redis

app = Flask("stock-service")

db: redis.Redis = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ["REDIS_PORT"]),
    password=os.environ["REDIS_PASSWORD"],
    db=int(os.environ["REDIS_DB"]),
)


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post("/item/create/<price>")
def create_item(price: int):
    item_id = db.incr("item_id")
    item_key = f"item:{item_id}"
    db.hmset(item_key, {"price": price, "stock": 0})
    return jsonify({"item_id": item_id}), 200


@app.get("/find/<item_id>")
def find_item(item_id: str):
    item_key = f"item:{item_id}"
    item_data = db.hgetall(item_key)
    if not item_data:
        return jsonify({"error": "Item not found"}), 400
    return (
        jsonify({"stock": int(item_data[b"stock"]), "price": int(item_data[b"price"])}),
        200,
    )


@app.post("/add/<item_id>/<amount>")
def add_stock(item_id: str, amount: int):
    item_key = f"item:{item_id}"
    if not db.exists(item_key):
        return jsonify({"error": "Item not found"}), 400
    db.hincrby(item_key, "stock", int(amount))
    return jsonify({"done": True}), 200


@app.post("/subtract/<item_id>/<amount>")
def remove_stock(item_id: str, amount: int):
    item_key = f"item:{item_id}"
    if not db.exists(item_key):
        return jsonify({"error": "Item not found"}), 400

    current_stock = int(db.hget(item_key, "stock"))
    if current_stock < int(amount):
        return jsonify({"error": "Insufficient stock"}), 400

    db.hincrby(item_key, "stock", -int(amount))
    return jsonify({"done": True}), 200

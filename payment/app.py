import os
import atexit
from flask import Flask, jsonify
import redis

app = Flask("payment-service")

db: redis.Redis = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ["REDIS_PORT"]),
    password=os.environ["REDIS_PASSWORD"],
    db=int(os.environ["REDIS_DB"]),
)


def close_db_connection():
    db.close()


atexit.register(close_db_connection)


@app.post("/create_user")
def create_user():
    user_id = db.incr("user_id")
    user_key = f"user:{user_id}"
    db.hmset(user_key, {"credit": 0})
    return jsonify({"user_id": user_id}), 200


@app.get("/find_user/<user_id>")
def find_user(user_id: str):
    user_key = f"user:{user_id}"
    user_data = db.hgetall(user_key)
    if not user_data:
        return jsonify({"error": "User not found"}), 400
    return jsonify({"user_id": int(user_id), "credit": int(user_data[b"credit"])}), 200


@app.post("/add_funds/<user_id>/<amount>")
def add_credit(user_id: str, amount: int):
    user_key = f"user:{user_id}"
    if not db.exists(user_key):
        return jsonify({"error": "User not found"}), 400
    db.hincrby(user_key, "credit", int(amount))
    return jsonify({"done": True}), 200


@app.post("/pay/<user_id>/<order_id>/<amount>")
def remove_credit(user_id: str, order_id: str, amount: int):
    user_key = f"user:{user_id}"
    order_key = f"order:{order_id}"
    current_credit = int(db.hget(user_key, "credit"))

    if current_credit < int(amount):
        return jsonify({"error": "Insufficient credit"}), 400

    db.hincrby(user_key, "credit", -int(amount))
    db.hset(order_key, "paid", "True")
    return jsonify({"status": "success"}), 200


@app.post("/cancel/<user_id>/<order_id>")
def cancel_payment(user_id: str, order_id: str):
    user_key = f"user:{user_id}"
    order_key = f"order:{order_id}"

    order_data = db.hgetall(order_key)
    if not order_data:
        return jsonify({"error": "Order not found"}), 400

    if order_data[b"paid"] == b"True":
        db.hset(order_key, "paid", "False")
        total_cost = int(order_data[b"total_cost"])
        db.hincrby(user_key, "credit", total_cost)
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"error": "Payment already cancelled"}), 400


@app.get("/status/<user_id>/<order_id>")
def payment_status(user_id: str, order_id: str):
    order_key = f"order:{order_id}"

    order_data = db.hgetall(order_key)
    if not order_data:
        return jsonify({"error": "Order not found"}), 400

    paid = True if order_data[b"paid"] == b"True" else False
    return jsonify({"paid": paid}), 200
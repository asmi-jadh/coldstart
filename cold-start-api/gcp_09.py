

from datetime import datetime


# -------------------------------
# 🔥 BACKEND MEMORY (VERY IMPORTANT)
# -------------------------------
last_time = None
last_request = 0
history_requests = []

# -------------------------------
# 🔥 FEATURE GENERATOR
# -------------------------------
def generate_features(hour, day, request_count, latency):
    global last_time, last_request, history_requests

    current_time = datetime.now()

    # Time difference
    if last_time is None:
        time_diff = 0
    else:
        time_diff = (current_time - last_time).total_seconds() / 60

    # Previous request
    prev_request = last_request

    # Rolling average
    history_requests.append(request_count)
    if len(history_requests) > 3:
        history_requests.pop(0)

    rolling_request = sum(history_requests) / len(history_requests)

    # Update memory
    last_time = current_time
    last_request = request_count

    return [hour, day, request_count, latency, time_diff, prev_request, rolling_request]


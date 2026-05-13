import math

vehicle_history = {}

FPS = 30

SCALE = 0.05

def calculate_speed(track_id, center):

    if track_id not in vehicle_history:
        vehicle_history[track_id] = []

    vehicle_history[track_id].append(center)

    if len(vehicle_history[track_id]) < 2:
        return 0

    p1 = vehicle_history[track_id][-2]
    p2 = vehicle_history[track_id][-1]

    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]

    distance = math.sqrt(dx*dx + dy*dy)

    speed = distance * SCALE * FPS

    return int(speed)
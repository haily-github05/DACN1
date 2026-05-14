import mysql.connector
from mysql.connector import Error
from datetime import datetime

class TrafficDatabase:
    def __init__(self):
        self.config = {
            "host": "127.0.0.1",
            "port": 3308, 
            "user": "root",
            "password": "", 
            "database": "traffic_db"
        }

    def get_connection(self):
        return mysql.connector.connect(**self.config)

    # --- 1. QUẢN LÝ BẢNG VEHICLES (Thông tin xe) ---
    def update_vehicle(self, plate, v_type):
        """Lưu hoặc cập nhật thông tin xe khi phát hiện"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO vehicles (license_plate, vehicle_type, last_seen)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE last_seen = %s, vehicle_type = %s
            """
            now = datetime.now()
            cursor.execute(query, (plate, v_type, now, now, v_type))
            conn.commit()
        except Error as e:
            print(f"Lỗi bảng Vehicles: {e}")
        finally:
            if conn.is_connected(): cursor.close(); conn.close()

    # --- 2. QUẢN LÝ BẢNG VIOLATIONS (Bằng chứng vi phạm) ---
    def log_violation(self, plate, v_type, v_error, img_path):
        """Lưu bằng chứng khi xe vi phạm luật"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = """
                INSERT INTO violations (license_plate, vehicle_type, violation_error, evidence_path, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (plate, v_type, v_error, img_path, datetime.now()))
            conn.commit()
        except Error as e:
            print(f"Lỗi bảng Violations: {e}")
        finally:
            if conn.is_connected(): cursor.close(); conn.close()

    # --- 3. QUẢN LÝ BẢNG TRAFFIC_LOGS (Thống kê lưu lượng) ---
    def add_log(self, v_type, lane_id=1):
        """Ghi nhận mọi lượt xe đi qua để làm báo cáo thống kê"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = "INSERT INTO traffic_logs (vehicle_type, lane_id, timestamp) VALUES (%s, %s, %s)"
            cursor.execute(query, (v_type, lane_id, datetime.now()))
            conn.commit()
        except Error as e:
            print(f"Lỗi bảng Logs: {e}")
        finally:
            if conn.is_connected(): cursor.close(); conn.close()
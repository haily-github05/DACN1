import mysql.connector
from datetime import datetime

class VehicleModel:
    def __init__(self, db_config):
        self.config = db_config

    def update_vehicle(self, license_plate, vehicle_type):
        conn = mysql.connector.connect(**self.config)
        cursor = conn.cursor()

        first_seen_timestamp = int(datetime.now().timestamp())

        query = """
            INSERT INTO vehicles (license_plate, vehicle_type, first_seen)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE vehicle_type = %s
        """

        cursor.execute(
            query,
            (license_plate, vehicle_type, first_seen_timestamp, vehicle_type)
        )

        conn.commit()
        cursor.execute(
        "SELECT vehicle_id FROM vehicles WHERE license_plate=%s",
        (license_plate,)
    )

        vehicle_id = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()

    # --------------------------------
    # 2. Lấy vehicle_id theo biển số
    # --------------------------------
    def get_vehicle_id(self, license_plate):
        conn = mysql.connector.connect(**self.config)
        cursor = conn.cursor()

        query = """
            SELECT vehicle_id
            FROM vehicles
            WHERE license_plate = %s
        """

        cursor.execute(query, (license_plate,))
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        if result:
            return result[0]
        return None

    # -------------------------------------------------
    # 3. HÀM QUAN TRỌNG (khuyên dùng) - get_or_create
    # -------------------------------------------------
    def get_or_create_vehicle(self, license_plate, vehicle_type):
        conn = mysql.connector.connect(**self.config)
        cursor = conn.cursor()

        # kiểm tra xe đã tồn tại chưa
        cursor.execute(
            "SELECT vehicle_id FROM vehicles WHERE license_plate=%s",
            (license_plate,)
        )

        result = cursor.fetchone()

        if result:
            vehicle_id = result[0]

            # update loại xe nếu cần
            cursor.execute(
                "UPDATE vehicles SET vehicle_type=%s WHERE vehicle_id=%s",
                (vehicle_type, vehicle_id)
            )
        else:
            # tạo mới
            first_seen_timestamp = int(datetime.now().timestamp())

            cursor.execute("""
                INSERT INTO vehicles (license_plate, vehicle_type, first_seen)
                VALUES (%s, %s, %s)
            """, (license_plate, vehicle_type, first_seen_timestamp))

            vehicle_id = cursor.lastrowid

        conn.commit()
        cursor.close()
        conn.close()

        return vehicle_id

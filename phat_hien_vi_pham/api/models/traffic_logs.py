import mysql.connector
from datetime import datetime

class TrafficLogModel:
    def __init__(self, db_config):
        self.config = db_config

    def add_log(self, vehicle_type, lane_id):
        conn = mysql.connector.connect(**self.config)
        cursor = conn.cursor()
        # log_id là varchar(100) theo hình của bạn
        log_id = f"LOG_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        query = """
            INSERT INTO traffic_logs (log_id, vehicle_type, lane_id)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (log_id, vehicle_type, lane_id))
        conn.commit()
        cursor.close()
        conn.close()
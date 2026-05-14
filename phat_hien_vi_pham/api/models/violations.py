import mysql.connector

class ViolationModel:
    def __init__(self, db_config):
        self.config = db_config

    def log_violation(self,vehicle_id, plate, v_type, video_id, image_path, status="pending"):
        conn = mysql.connector.connect(**self.config)
        cursor = conn.cursor()

        query = """
            INSERT INTO violations (vehicle_id, plate, type, video_id, image, status)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (vehicle_id, plate, v_type, video_id, image_path, status))
        conn.commit()

        cursor.close()
        conn.close()
        
    def get_all_violations(self):

        conn = mysql.connector.connect(
            **self.config
        )

        cursor = conn.cursor(
            dictionary=True
        )

        query = """
            SELECT 
                v.id,
                v.vehicle_id,
                v.type,
                v.time,
                v.video_id,
                v.plate,
                v.image,
                v.status,

                ve.vehicle_type

            FROM violations v

            LEFT JOIN vehicles ve
            ON v.vehicle_id = ve.vehicle_id

            ORDER BY v.time DESC
        """

        cursor.execute(query)

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return data
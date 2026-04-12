import mysql.connector

class ViolationModel:
    def __init__(self, db_config):
        self.config = db_config

    # ======================
    # ➕ INSERT VIOLATION
    # ======================
    def log_violation(self, v_type, camera, plate, image_path, status="NEW"):
        conn = mysql.connector.connect(**self.config)
        cursor = conn.cursor()

        query = """
            INSERT INTO violations (type, camera, plate, image, status)
            VALUES (%s, %s, %s, %s, %s)
        """

        cursor.execute(query, (v_type, camera, plate, image_path, status))
        conn.commit()

        cursor.close()
        conn.close()

    # ======================
    # 📊 GET ALL VIOLATIONS
    # ======================
    def get_all_violations(self):
        conn = mysql.connector.connect(**self.config)
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                id,
                type,
                time,
                camera,
                plate,
                image,
                status
            FROM violations
            ORDER BY time DESC
        """

        cursor.execute(query)
        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return data
import sqlite3

def fetch_task_metrics(task_id):
    conn = sqlite3.connect("data/metrics.db")
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT start_time, end_time, duration
            FROM task_metrics
            WHERE task_id = ?
        """, (task_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "start_time": row[0],
                "end_time": row[1],
                "duration": row[2]
            }
        else:
            return None

    except Exception as e:
        conn.close()
        return None

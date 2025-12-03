import sqlite3
import logging
import sys
import time
import paho.mqtt.client as mqtt
import os

class FailureManager:
    def __init__(self, db_path, threshold):
        self.db_path = db_path
        self.threshold = threshold
        self.fail_count = 0
        self._init_db()

    def _init_db(self):
        """Creates the table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS failed_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        topic TEXT NOT NULL,
                        payload TEXT NOT NULL,
                        created_at INTEGER
                    )
                ''')
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")

    def buffer_data(self, topic, payload):
        try:
            with sqlite3.connect(self.db_path) as conn:
                timestamp = int(time.time())
                conn.execute(
                    'INSERT INTO failed_queue (topic, payload, created_at) VALUES (?, ?, ?)', 
                    (topic, payload, timestamp)
                )
            
            self.fail_count += 1
            logging.warning(f"Message buffered locally. Failure count: {self.fail_count}/{self.threshold}")
            
            if self.fail_count >= self.threshold:
                logging.critical("Failure threshold reached. Exiting to trigger Systemd restart.")
                time.sleep(1)
                os._exit(1)
                
        except Exception as e:
            logging.error(f"CRITICAL: Could not write to local SQLite DB: {e}")

    def recover_data(self, client):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT id, topic, payload FROM failed_queue ORDER BY id ASC')
                rows = cursor.fetchall()
                
                if not rows:
                    return

                logging.info(f"Recovery mode: Attempting to publish {len(rows)} buffered messages...")
                
                for row_id, topic, payload in rows:
                    res = client.publish(topic, payload)
                    
                    if res.rc == mqtt.MQTT_ERR_SUCCESS:
                        conn.execute('DELETE FROM failed_queue WHERE id = ?', (row_id,))
                    else:
                        logging.warning("Recovery connection unstable. Stopping recovery loop.")
                        break 
                        
                logging.info("Recovery loop finished.")
                
        except Exception as e:
            logging.error(f"Error during recovery: {e}")
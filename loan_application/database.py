import mysql.connector
import logging
import time


DB_HOST = "sql6.freemysqlhosting.net"
DB_PORT = "3306"
DB_USER = "sql6695309"
DB_PASSWORD = "XuhtFQmSx7"
DB_NAME = "sql6695309"

# Configure logger
logger = logging.getLogger(__name__)

class DatabaseConnection:

  def __init__(self):
    self.connection = None

  def connect(self):
    self.connection = mysql.connector.connect(
      user=DB_USER, 
      password=DB_PASSWORD, 
      host=DB_HOST,
      port=DB_PORT,
      database=DB_NAME
    )

  def close(self):
    if self.connection:
      self.connection.close()

  def execute_query(self, query, params=None):
    cursor = self.connection.cursor()

    try:
      cursor.execute(query, params)
      self.connection.commit()
      
      # for insert query return the id of the last inserted row
      if "INSERT" in query:
        return cursor.lastrowid # the id of the last inserted row
      elif "SELECT" in query:
        return cursor.fetchall() # returns a list of tuples containing the rows data -> Eg: [("Jim", "98764325"), ("John", "98764325")]
      elif "UPDATE" in query or "DELETE" in query:
        query_parts = query.split()
        loan_id_index = query_parts.index("loan_id")
        return query_parts[loan_id_index + 1] # returns the id of the row updated
    except Exception as e:
      logger.error(f"Error: Error saving loan application data to db: {e}")
      return None
    finally:
      # Close the cursor
      cursor.close()
import mysql.connector
import logging


DB_HOST = "sql6.freemysqlhosting.net"
DB_PORT = "3306"
DB_USER = "sql6695309"
DB_PASSWORD = "XuhtFQmSx7"
DB_NAME = "sql6695309"

# Configure logger
logger = logging.getLogger(__name__)

class InvalidLoanIdException(Exception): #Exception for invalid loan id
    pass

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
      # for insert query return the id of the last inserted row
      if "INSERT" in query:
        self.connection.commit()
        return cursor.lastrowid # the id of the last inserted row
      elif "SELECT" in query:
        try:
          all_rows = cursor.fetchall()
          return  all_rows # returns a list of tuples containing the rows data -> Eg: [("Jim", "98764325"), ("John", "98764325")]
        except Exception as e:
          logger.error(f"Error occured executing function cursor.fetchall(): {e}")
          return None
      elif "UPDATE" in query or "DELETE" in query:
        self.connection.commit()
        query_parts = query.split()
        if (params == None):
          loan_id_index = query_parts.index("loan_id")
          loan_id = query_parts[loan_id_index + 2]
        else:
          '''
            Sample UPDATE query: UPDATE loan_application SET application_name=%s WHERE loan_id=%s
            In the params array, the last element will be the loan_id
          '''
          loan_id = params[len(params) -1] # last element in the array is the id
        
        # checking if the loan_id in the update or delete query is valid or not by querying the db
        select_query = f"SELECT * FROM loan_application WHERE loan_id = {loan_id}"
        cursor.execute(select_query, None)
        if (not cursor.fetchall()): #when nothing is returned that means the id is invalid, so raise exception
          raise InvalidLoanIdException
        
        return  loan_id# returns the id of the row updated or deleted
    except Exception as e:
      if (isinstance (e, InvalidLoanIdException)):
        logger.error(f"Error: Invalid loan id encountered")
      else:
        logger.error(f"Error: Database error occured: {e}")
      return None
    finally:
      # Close the cursor
      cursor.close()
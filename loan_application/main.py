from enum import Enum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import DatabaseConnection
from kombu import Connection, Producer, Queue
import logging
import json
from typing import Any

# Configure a logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = FastAPI()

class EmploymentStatus(Enum):
    UNEMPLOYED = "unemployed"
    SELF_EMPLOYED = "self-employed"
    EMPLOYED = "employed"

class LoanStatus(Enum):
    IN_PROGRESS = "in-progress"
    APPROVED = "approved"
    NOT_APPROVED = "not approved"

class LoanApplication(BaseModel):
    applicant_name: str
    credit_score: int
    loan_amount: float
    loan_purpose: str
    income: float
    employment_status: EmploymentStatus
    debt: float

    def post_data_to_db(self, db_connection):  # Pass connection as an argument
        query = f'''INSERT INTO loan_application 
                VALUES (NULL, "{self.applicant_name}", {self.credit_score}, {self.loan_amount}, "{self.loan_purpose}", 
                {self.income}, "{self.employment_status.value}", {self.debt}, "{LoanStatus.IN_PROGRESS.value}")'''
        return db_connection.execute_query(query)


# Posting the loan application data to the database + publishing it to loan_application queue
@app.post("/post/loan-application", status_code=200)
def post_loan_application_data(loan_data: LoanApplication):
    if not loan_data:
        raise HTTPException(status_code=400, detail=f"Missing data")
    logger.info(f"Received loan application data for {loan_data.applicant_name}")

    # Creating database connection + queue connection
    db_connection = DatabaseConnection()
    db_connection.connect()
    queue_connection = Connection('amqp://guest:guest@localhost:5672')

    # Declaring flags to track success for saving data to db & publishing to queue
    db_save_success_flag = False
    queue_publish_success_flag = False

    # Saving data to database
    try:
        loan_id_after_data_post = loan_data.post_data_to_db(db_connection) # function returns the id of the inserted row in db
        logger.info(f"Success: Loan data successfully saved to db for applicant: {loan_data.applicant_name}")
        db_save_success_flag = True #set flag to true on successfully saving data to db
    except Exception as e:
        logger.error(f"Error: Error saving loan application data to db for applicant {loan_data.applicant_name}: {e}")
    finally:
        # Close the database connection
        db_connection.close()
        logger.info(f"Info: Database connection closed for applicant: {loan_data.applicant_name}")
    
    # Publish data to queue
    try:
        loan_data_json = json.loads(loan_data.model_dump_json())
        loan_data_json["loan_id"] = loan_id_after_data_post # adding the loan_id to post to queue so that it can be identified
        
        publish_data_to_loan_queue(loan_data_json, queue_connection)
        
        logger.info(f"Success: Loan data successfully published to loan queue for applicant: {loan_data.applicant_name}")
        
        queue_publish_success_flag = True #set flag to true on successfully publishing to queue
    except Exception as e:
        logger.error(f"Error: Error publishing loan application data for applicant {loan_data.applicant_name}: {e}")
    finally:
        # Close the queue connection
        queue_connection.close()
        logger.info(f"Info: Queue connection closed for applicant: {loan_data.applicant_name}")
    
    # Final return message based on saving to db & publishing to queue
    if db_save_success_flag and queue_publish_success_flag:
        return {"message": f"Success! Loan data saved to db & published to queue for applicant: {loan_data.applicant_name}"}
    elif not db_save_success_flag and queue_publish_success_flag:
        return {"message": f"Partial success!  Loan data NOT saved to db; published to queue for applicant: {loan_data.applicant_name}"}
    elif db_save_success_flag and not queue_publish_success_flag:
        return {"message": f"Partial success!  Loan data saved to db; NOT published to queue for applicant: {loan_data.applicant_name}"}
    else:
        return {"message": f"Failure! Loan data couldn't be saved to db or published to queue for applicant: {loan_data.applicant_name}"}

def publish_data_to_loan_queue(loan_data, queue_connection):
    # Creating a producer channel
    channel = queue_connection.channel()
    producer = Producer(channel)

    # Publish the data to loan_applications queue
    producer.publish(loan_data, exchange='', routing_key='loan_applications', delivery_mode=2)

@app.get("/get/all/loan-applications", status_code=200)
def get_all_loan_applications():
    try:
        # Creating database connection
        db_connection = DatabaseConnection()
        db_connection.connect()
        query = "SELECT * FROM loan_application;"
        loan_data = db_connection.execute_query(query) # returns an array of tuples
        logger.info(f"Success! All loan data retrived from db")
        return loan_data
    except Exception as e:
            logger.error(f"Error: Error fetching all loan data: {e}")
            raise HTTPException(status_code=400, detail=f"Error occured while fetching data")
    finally:
        # Close the database connection
        db_connection.close()
        logger.info(f"Info: Database connection closed for get all request")

@app.delete("/delete/loan-data/{loan_id}", status_code=200) # deletes SINGLE entry by loan_id
def delete_loan_data_by_id(loan_id: int):
    if (not loan_id):
        logger.error("loan_id parameter missing from delete request!") # for the server
        raise HTTPException(status_code=400, detail=f"Bad request! loan_id parameter missing from request!") # for the client
    try:
        # Creating database connection
        db_connection = DatabaseConnection()
        db_connection.connect()
        query = f"DELETE FROM loan_application WHERE loan_id = {loan_id}"
        loan_data = db_connection.execute_query(query) # returns an array of tuples
        logger.info(f"Success! Loan data of id:{loan_id} deleted.")
        return {"message": f"Success! Loan data of id:{loan_id} deleted."}
    except Exception as e:
            logger.error(f"Error: Error deleting loan data of id:{loan_id}: {e}")
            raise HTTPException(status_code=400, detail=f"Error occured while deleting data")
    finally:
        # Close the database connection
        db_connection.close()
        logger.info(f"Info: Database connection closed for delete request for loan_id: {loan_id}")

@app.put("/update/loan_data", status_code=200) # updates SINGLE entry by loan_id
def update_loan_data(loan_data: dict[str, Any]):
    if not loan_data['loan_id']:
        logger.error("loan_id parameter missing from update request!") # for the server
        raise HTTPException(status_code=400, detail=f"Missing loan id for update") # for the client
    logger.info(f"Updating loan application data for loan id {loan_data['loan_id']}")
    try:
        # Creating database connection
        db_connection = DatabaseConnection()
        db_connection.connect()

        # Example query: query = f"UPDATE loan_application SET loan_status = \"{loan_data['loan_status']}\" WHERE loan_id = {loan_data['loan_id']};"
        
        query = "UPDATE loan_application SET "
        params = []

        for key, value in loan_data.items():
            if key != "loan_id":
                query += f"{key} = %s,"
                params.append(value)

        query = query[:-1]  # Remove the trailing comma
        query += f" WHERE loan_id = %s;"  # Add loan_id with placeholder
        params.append(loan_data["loan_id"])
        updated_row_index = db_connection.execute_query(query, params) # the index of the row updated
        
        logger.info(f"Success! Data updated in db for loan id: {updated_row_index}")
        
        return {"message": f"Success! Data updated in db for loan id: {updated_row_index}"}
    except Exception as e:
            logger.error(f"Error: Error updating loan data for id {updated_row_index}: {e}")
            raise HTTPException(status_code=400, detail=f"Error occured while updating data")
    finally:
        # Close the database connection
        db_connection.close()
        logger.info(f"Info: Database connection closed for update request for loan id: {updated_row_index}")

    

    


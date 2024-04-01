from enum import Enum
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import DatabaseConnection
from kombu import Connection, Producer
import logging
import json

# Configure a logger
logger = logging.getLogger(__name__)

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
@app.post("/loan-application", status_code=200)
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
    producer.publish(loan_data, exchange='', routing_key='loan_applications')
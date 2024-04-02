from kombu import Connection, Producer, Queue
import logging
from loan_application.database import DatabaseConnection

# Configure a logger
logger = logging.getLogger(__name__)


def update_loan_status_in_db(message):
    loan_data = message.payload

    # Process the loan data (e.g., validate, save to database)
    logger.info(f"Updating loan status in db for: {loan_data.applicant_name}")
    
    

    # Publish the data to loan_approval_results queue
    try:
        # Creating database connection + queue connection
        db_connection = DatabaseConnection()
        db_connection.connect()
        query = f"UPDATE loan_application SET loan_status = {loan_data.loan_status} WHERE loan_id = {loan_data.loan_id};"
        db_connection.execute_query(query)
        message.ack() # sending ack to queue so that it can now remove the message after processing
    except Exception as e:
        logger.error(f"Error: Error updating loan application data for applicant {loan_data.applicant_name}: {e}")
    finally:
        # Close the database connection
        db_connection.close()
        logger.info(f"Info: Database connection closed for applicant: {loan_data.applicant_name}")


queue_connection_string = 'amqp://guest:guest@localhost:5672//'
queue_connection = Connection(queue_connection_string)

loan_approval_results_queue = Queue(name='loan_approval_results', connection=queue_connection)

# Create a consumer object
consumer = queue_connection.Consumer(queues=[loan_approval_results_queue])

# Consume messages from the queue and call the callback function for each message
consumer.consume(callbacks=[update_loan_status_in_db])

# Start consuming messages (non-blocking)
worker = consumer.serve()
worker.wait()
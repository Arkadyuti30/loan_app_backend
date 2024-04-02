from kombu import Connection, Producer, Queue
from fastapi import FastAPI
import logging
from loan_application.main import LoanStatus

# Configure a logger
logger = logging.getLogger(__name__)

app = FastAPI()

def process_loan_approval(message):
    loan_data = message.payload

    # Process the loan data (e.g., validate, save to database)
    logger.info(f"Received risk score for: {loan_data.applicant_name}. Processing loan approval!")
    
    # Criterea for loan approval
    '''
        Risk score negative or less than 50 --> not approved
        Risk score within 50 to 70 but purpose is wedding or personal --> not approved
        Risk score within 50 to 70 but purpose is NOT wedding or personal --> approved
        Risk score above 70 --> approved
    '''
    if 0 < loan_data.risk_score < 50:
        loan_data["loan_status"] = LoanStatus.NOT_APPROVED.value
    elif 50 <= loan_data.risk_score < 70:
        if "WEDDING" in loan_data.loan_purpose.upper() or "PERSONAL" in loan_data.loan_purpose.upper() or "BUSINESS" in loan_data.loan_purpose.upper():
            loan_data["loan_status"] = LoanStatus.NOT_APPROVED.value
        else:
            loan_data["loan_status"] = LoanStatus.APPROVED.value
    elif loan_data.risk_score > 70:
        loan_data["loan_status"] = LoanStatus.APPROVED.value
    
    # Creating a producer channel
    channel = queue_connection.channel()
    producer = Producer(channel)

    # Publish the data to loan_approval_results queue
    try:
        producer.publish(loan_data, exchange='', routing_key='loan_approval_results') 
        message.ack() # sending ack to queue so that it can now remove the message after processing
    except Exception as e:
        logger.error(f"Error: Error publishing data to loan_approval_results queue for applicant {loan_data.applicant_name}: {e}")


queue_connection_string = 'amqp://guest:guest@localhost:5672//'
queue_connection = Connection(queue_connection_string)

risk_assessment_results_queue = Queue(name='risk_assessment_results', connection=queue_connection)

# Create a consumer object
consumer = queue_connection.Consumer(queues=[risk_assessment_results_queue])

# Consume messages from the queue and call the callback function for each message
consumer.consume(callbacks=[process_loan_approval])

# Start consuming messages (non-blocking)
worker = consumer.serve()
worker.wait()
from kombu import Connection, Producer, Queue
from fastapi import FastAPI
import logging

# Configure a logger
logger = logging.getLogger(__name__)

app = FastAPI()

def process_loan_application(message):
    loan_data = message.payload

    # Process the loan data (e.g., validate, save to database)
    logger.info(f"Received loan application for: {loan_data.applicant_name}. Calculating risk score!")
    risk_score = calculate_risk(loan_data)

    # add risk_score to loan_data
    loan_data["risk_score"] = risk_score

    # Creating a producer channel
    channel = queue_connection.channel()
    producer = Producer(channel)

    # Publish the data to risk_assessment_results queue

    try:
        producer.publish(loan_data, exchange='', routing_key='risk_assessment_results') 
        message.ack() # sending ack to queue so that it can now remove the message after processing
    except Exception as e:
        logger.error(f"Error: Error publishing data to risk_assessment_results queue for applicant {loan_data.applicant_name}: {e}")

def calculate_risk(loan_data):
    risk_score = 100 #initial value, it's decreased based on potential risks
  
    # based on credit score
    if 300 < loan_data.credit_score < 500:
      risk_score -= 5
    elif loan_data.credit_score < 300:
        risk_score -= 10
    
    #based on debt to income ratio
    debt_to_income_ratio = loan_data.debt/loan_data.income

    if 1 <= debt_to_income_ratio <= 5:
        risk_score -= 10
    elif 6 <= debt_to_income_ratio <= 10:
        risk_score -= 20
    elif 11 <= debt_to_income_ratio <= 15:
        risk_score -= 30
    elif debt_to_income_ratio > 15:
        risk_score -= 40
    
    # based on employment status
    if loan_data.employment_status == "unemployed":
        risk_score -= 20
    elif loan_data.employment_status == "self-employed":
        risk_score -= 10
    
    # based on loan amount - loan amount should be less than the current debt if debt to income ratio is greater than 1
    if loan_data.loan_amount > loan_data.debt and debt_to_income_ratio > 1:
        risk_score -= 20
    
    # based on loan purpose
    if "BUSINESS" in loan_data.loan_purpose.upper() or "PERSONAL" in loan_data.loan_purpose.upper():
        risk_score -= 5
    elif "WEDDING" in loan_data.loan_purpose.upper():
        risk_score -= 15
    
    return risk_score

queue_connection_string = 'amqp://guest:guest@localhost:5672//'
queue_connection = Connection(queue_connection_string)

loan_applications_queue = Queue(name='loan_applications', connection=queue_connection)

# Create a consumer object
consumer = queue_connection.Consumer(queues=[loan_applications_queue])

# Consume messages from the queue and call the callback function for each message
consumer.consume(callbacks=[process_loan_application])

# Start consuming messages (non-blocking)
worker = consumer.serve()
worker.wait()

from kombu import Connection, Consumer, Producer, Queue, exceptions
from kombu.mixins import ConsumerProducerMixin
from kombu.exceptions import ChannelError
from pika.exceptions import ConnectionClosed
import logging
import json
import time

# Configure a logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

queue_connection_params = {'host': 'localhost', 'port': 5672, 'userid': 'guest', 'password': 'guest'}

class RiskAssessmentService(ConsumerProducerMixin):

    def __init__(self):
        # Reconnection logic
        self.connection = None
        self.reconnect()

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(
                queues=Queue('loan_applications'),
                on_message=self.process_loan_application
            )
        ]

    def process_loan_application(self, message):
        try:
            raw_body = message.body
            loan_data = json.loads(raw_body)

            # Process the loan data (e.g., validate, save to database)
            logger.info(f"Received loan application for: {loan_data['applicant_name']}. Calculating risk score!")
            risk_score = calculate_risk(loan_data)

            # add risk_score to loan_data
            loan_data['risk_score'] = risk_score

            # Publish the data to risk_assessment_results queue
            try:
                self.producer.publish(
                    loan_data,
                    exchange='',  # Use default exchange for direct routing
                    routing_key='risk_assessment_results',
                    delivery_mode=2,  # Persistent delivery (optional)
                )
                message.ack() # sending ack to queue so that it can now remove the message after processing
            except Exception as e:
                logger.error(f"Error: Error publishing data to risk_assessment_results queue for applicant {loan_data.applicant_name}: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON message body: {e}")


    def reconnect(self):
        while True:
            try:
                self.connection = Connection(**queue_connection_params)
                logger.info("Connected to message broker!")
                break
            except (ConnectionClosed, ChannelError) as e:
                logger.warning(f"Connection error: {e}. Retrying in 5 seconds...")
                time.sleep(5)

def calculate_risk(loan_data):
    risk_score = 100 #initial value, it's decreased based on potential risks
  
    # based on credit score
    if 300 < loan_data['credit_score'] < 500:
      risk_score -= 5
    elif loan_data['credit_score'] < 300:
        risk_score -= 10
    
    #based on debt to income ratio
    debt_to_income_ratio = loan_data['debt']/loan_data['income']

    if 1 <= debt_to_income_ratio <= 5:
        risk_score -= 10
    elif 6 <= debt_to_income_ratio <= 10:
        risk_score -= 20
    elif 11 <= debt_to_income_ratio <= 15:
        risk_score -= 30
    elif debt_to_income_ratio > 15:
        risk_score -= 40
    
    # based on employment status
    if loan_data['employment_status'] == "unemployed":
        risk_score -= 20
    elif loan_data['employment_status'] == "self-employed":
        risk_score -= 10
    
    # based on loan amount - loan amount should be less than the current debt if debt to income ratio is greater than 1
    if loan_data['loan_amount'] > loan_data['debt'] and debt_to_income_ratio > 1:
        risk_score -= 20
    
    # based on loan purpose
    if "BUSINESS" in loan_data['loan_purpose'].upper() or "PERSONAL" in loan_data['loan_purpose'].upper():
        risk_score -= 5
    elif "WEDDING" in loan_data['loan_purpose'].upper():
        risk_score -= 15
    
    return risk_score


if __name__ == "__main__":
    service = RiskAssessmentService()
    service.run()

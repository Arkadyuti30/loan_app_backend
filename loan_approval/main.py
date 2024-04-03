from kombu import Connection, Consumer, Producer, Queue, exceptions
from kombu.mixins import ConsumerProducerMixin
from kombu.exceptions import ChannelError
from pika.exceptions import ConnectionClosed
import logging
import json
import time
from loan_status import LoanStatus

# Configure a logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

queue_connection_params = {'host': 'localhost', 'port': 5672, 'userid': 'guest', 'password': 'guest'}

class LoanApprovalService(ConsumerProducerMixin):
    def __init__(self):
        # Reconnection logic
        self.connection = None
        self.reconnect()

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(
                queues=Queue('risk_assessment_results'),
                on_message=self.process_loan_approval
            )
        ]
    
    def process_loan_approval(self, message):
        try:
            raw_body = message.body
            loan_data = json.loads(raw_body)

            # Process the loan data (e.g., validate, save to database)
            logger.info(f"Received risk score for: {loan_data['applicant_name']}. Processing loan approval!")
    
            # Criterea for loan approval
            '''
                Risk score negative or less than 50 --> not approved
                Risk score within 50 to 70 but purpose is wedding or personal --> not approved
                Risk score within 50 to 70 but purpose is NOT wedding or personal --> approved
                Risk score above 70 --> approved
            '''
            if 0 < loan_data['risk_score'] < 50:
                loan_data['loan_status'] = LoanStatus.NOT_APPROVED.value
            elif 50 <= loan_data['risk_score'] < 70:
                if "WEDDING" in loan_data['loan_purpose'].upper() or "PERSONAL" in loan_data['loan_purpose'].upper() or "BUSINESS" in loan_data['loan_purpose'].upper():
                    loan_data['loan_status'] = LoanStatus.NOT_APPROVED.value
                else:
                    loan_data['loan_status'] = LoanStatus.APPROVED.value
            elif loan_data['risk_score'] > 70:
                loan_data['loan_status'] = LoanStatus.APPROVED.value

            # Publish the data to loan_approval_results queue
            try:
                self.producer.publish(
                    loan_data,
                    exchange='',  # Use default exchange for direct routing
                    routing_key='loan_approval_results',
                    delivery_mode=2,  # Persistent delivery (optional)
                )
                message.ack() # sending ack to queue so that it can now remove the message after processing
            except Exception as e:
                logger.error(f"Error: Error publishing data to loan_approval_results queue for applicant {loan_data['applicant_name']}: {e}")
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

if __name__ == "__main__":
    service = LoanApprovalService()
    service.run()
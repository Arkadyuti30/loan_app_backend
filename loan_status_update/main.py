from kombu import Connection, Queue, Consumer
from kombu.mixins import ConsumerMixin
from kombu.exceptions import ChannelError
from pika.exceptions import ConnectionClosed
import logging
from database import DatabaseConnection
import time

# Configure a logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class LoanStatusUpdateService(ConsumerMixin):
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None  # Initialize connection attribute
        self.reconnect()  # Attempt reconnection on initialization

    def get_consumers(self, Consumer, channel):
        return [
            Consumer(
                queues=[Queue(name='loan_approval_results', connection=self.connection)],
                callbacks=[self.update_loan_status_in_db]
            )
        ]

    def update_loan_status_in_db(self, body, message):
        loan_data = body

        # Process the loan data (e.g., validate, save to database)
        logger.info(f"Updating loan status in db for: {loan_data['applicant_name']}")

        try:
            # Database connection within update_loan_status_in_db
            db_connection = DatabaseConnection()
            db_connection.connect()
            query = f"UPDATE loan_application SET loan_status = \"{loan_data['loan_status']}\" WHERE loan_id = {loan_data['loan_id']};"
            print("QUERY: ", query)
            loan_id = db_connection.execute_query(query)
            logger.info(f"Success! Loan status updated in db for loan id: {loan_id}")
            message.ack()  # sending ack to queue so that it can now remove the message after processing
        except Exception as e:
            logger.error(f"Error: Error updating loan application data for applicant {loan_data['applicant_name']}: {e}")
        finally:
            # Close the database connection
            db_connection.close()
            logger.info(f"Info: Database connection closed for applicant: {loan_data['applicant_name']}")
    def reconnect(self):
        while True:
            try:
                self.connection = Connection(self.connection_string)
                logger.info("Connected to message broker!")
                break
            except (ConnectionClosed, ChannelError) as e:
                logger.warning(f"Connection error: {e}. Retrying in 5 seconds...")
                time.sleep(5)


if __name__ == "__main__":
    queue_connection_string = 'amqp://guest:guest@localhost:5672//'
    updater = LoanStatusUpdateService(queue_connection_string)
    updater.run()  # Start consuming messages
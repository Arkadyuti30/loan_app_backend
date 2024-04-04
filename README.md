# loan_app_backend
This is the backend for a loan approval app consisting of 4 microservices.

## Steps to steup the backend in your local:
1. Clone the repo
2. Make sure you have Docker Desktop installed. If not, install from https://www.docker.com/products/docker-desktop/ for your OS
3. Open 5 terminals in loan_app_backend (repo)
   - In terminal 1 run, // Rabbit MQ
     - `docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management`
     - This is for running RabbitMQ message broker
     - `pip install pika`
   - In terminal 2 run, // Loan Application Microservice
      `cd loan_application`
     `pip install -r requirements.txt`
      `uvicorn main:app --reload`
   - In terminal 3 run, // Risk assessment
     `cd risk_assessment`
     `pip install -r requirements.txt`
     `python3 main.py`

    - In terminal 4 run, // Loan Approval
     `cd loan_approval`
      `pip install -r requirements.txt`
     `python3 main.py`

   - In terminal 3 run, // Loan Status Update
     `cd loan_status_update`
     `pip install -r requirements.txt`
     `python3 main.py`
4. Go to your browser & open this url // RabbitMQ UI
   `http://localhost:15672/`
   Enter username & password as `guest`
5. Create 3 queues in the RabbitMQ UI
![image](https://github.com/Arkadyuti30/loan_app_backend/assets/22547304/764d244c-5f10-4d27-b4e8-cc4125dd5a6f)
- Click on "Queues and Streams" on top
- Click on "Add a new queue"
- Just enter the name (no other details required)
- Click "Add queue" button at the bottom
Create 3 queues with the following names, names should be EXACT as mentioned here:
  - loan_applications
  - loan_approval_results
  - risk_assessment_results

Congratulation! Backend setup is now complete!
For the frontend steup go to this repo: https://github.com/Arkadyuti30/loan_app_ui

## Video Demo
Here's a demo video of the whole app: https://www.loom.com/share/96842ad65c264c74912e464802c2a154?sid=0b776d04-a7c2-4ba1-935b-cc6b029007c5

### The backend has 4 microservices:
   - LoanApplication --> This has 4 APIs
      - /post/loan-application -- Posts loan data to database and loan_applications queue for further processing
      - /get/all/loan-applications -- Returns all the loan applications present in the db
      - /delete/loan-data/{loan_id} - Accepts loan_id as parameter and deletes that row (one entry only)
      - /update/loan_data - Based on the loan_id passed to its request body, it updates that row (one entry only)
   
   - RiskAssessmentService --> It's a consumer cum producer.
      - Consumes loan data from `loan_applications` queue
      - Calculates risk score
      - Produces to `risk_assessment_results` queue for further computation
    
   - LoanApprovalService --> It's a consumer cum producer.
      - Consumes loan data from `risk_assessment_results` queue
      - Calculates whether the loan is approved or not based on certain criteria
      - Produces to `loan_approval_results` queue for updating loan_status in db
   - LoanStatusUpdateService --> It's a consumer.
      - Consumes loan data from `loan_approval_results` queue
      - Updates the loan_status for that loan in db
   The whole idea behind this was to have a loosely coupled system that is robust and has higher availability.

Here's the architecture diagram:
![image](https://github.com/Arkadyuti30/loan_app_backend/assets/22547304/39c69774-f50a-43d0-b3ea-2922720e6d64)



### Tech Stack:
- API Framework: Python Fast API
- Message broker: RabbitMQ
- Database: MySQL


# loan_app_backend
This is the backend for a loan approval app consisting of 4 microservices.

## Steps to steup the backend in your local:
1. Clone the repo
2. Make sure you have Docker Desktop installed. If not, install from https://www.docker.com/products/docker-desktop/ for your OS
3. Open 5 terminals in loan_app_backend (repo)
   - In terminal 1 run, // Rabbit MQ
     `docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.13-management`
     // This is for running RabbitMQ message broker
   - In terminal 2 run, // Loan Application Microservice
      `cd loan_application`
      `uvicorn main:app --reload`
   - In terminal 3 run, // Risk assessment
     `cd risk_assessment`
     `python3 main.py`

    - In terminal 4 run, // Loan Approval
     `cd loan_approval`
     `python3 main.py`

   - In terminal 3 run, // Loan Status Update
     `cd loan_status_update`
     `python3 main.py`
4. Go to your browser & open this url // RabbitMQ UI
   `http://localhost:15672/`
   Enter username & password as `guest`
5. Create 3 queues in the RabbitMQ UI
![image](https://github.com/Arkadyuti30/loan_app_backend/assets/22547304/764d244c-5f10-4d27-b4e8-cc4125dd5a6f)
- Click on "Queues and Streams" on top
- Click on "Add a new queue"
- Just enter the name
- Click "Add queue" button at the bottom
Create 3 queues with the following names, names should be EXACT as mentioned here:
  - loan_applications
  - loan_approval_results
  - risk_assessment_results

Congratulation! Backend setup is now complete!
For the frontend steup go to this repo: https://github.com/Arkadyuti30/loan_app_ui
 


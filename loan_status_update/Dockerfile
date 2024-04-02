FROM python:3.10.12

WORKDIR /loan_application


COPY requirements.txt ./
RUN pip install -r requirements.txt

CMD ["uvicorn", "main:app", "--reload", "--port", "8001"]
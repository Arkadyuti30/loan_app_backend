import requests

data = {
    "loan_data": {
        "applicant_name": "Ramesh",
        "credit_score": 700,
        "loan_amount": 800000.00,
        "loan_purpose": "New business",
        "income": 500000,
        "employment_status": "self-employed",
        "debt": 250000.00
    }
}

response = requests.post("http://127.0.0.1:8000/loan-application", json=data)

# Check for successful response (optional)
if response.status_code == 200:
  # Process the successful response (assuming JSON)
  response_data = response.json()
  print(response_data)
else:
  # Handle error (non-200 status code)
  print(f"Error: {response.status_code}, {response.text}")

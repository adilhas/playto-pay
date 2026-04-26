import threading
import requests

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc3MjQyMTkzLCJpYXQiOjE3NzcyMjA1OTMsImp0aSI6IjkwZDIxNDkxMmQ1MDQ1NjdhYzQyZDhhM2ZlYTM3MjUzIiwidXNlcl9pZCI6IjEifQ.5RUviJFt57WmLj3F2cTF9IuSw2497mRF37u2_tPR7NQ"


def make_request():
    res = requests.post(
        "http://127.0.0.1:8000/api/v1/payouts/",
        json={"amount_paise": 60000, "bank_account_id": 1},
        headers={"Authorization": f"Bearer {TOKEN}"},
    )
    print(res.json())


t1 = threading.Thread(target=make_request)
t2 = threading.Thread(target=make_request)

t1.start()
t2.start()

t1.join()
t2.join()

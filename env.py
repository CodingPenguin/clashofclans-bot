import os

API_KEY = os.environ["API_KEY"]
TOKEN = os.environ["TOKEN"]
PROXIES = {
    "http": os.environ['QUOTAGUARD_STATIC_URL'],
    "https": os.environ['QUOTAGUARD_STATIC_URL']
}   
MONGO_SRV_URL = os.environ['MONGO_SRV_URL']
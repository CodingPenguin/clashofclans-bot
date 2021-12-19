import os

API_KEY = os.environ.get("API_KEY")
TOKEN = os.environ.get("TOKEN")
PROXIES = {
    "http": os.environ.get('QUOTAGUARD_STATIC_URL'),
    "https": os.environ.get('QUOTAGUARD_STATIC_URL')
}   
MONGO_SRV_URL = os.environ.get('MONGO_SRV_URL')
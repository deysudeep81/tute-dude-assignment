from pymongo import MongoClient

try:
    client = MongoClient("mongodb+srv://deysudeep81_db_user:oxKsEDRTjjrqVzWA@flasktudedude.m9pktx3.mongodb.net/?retryWrites=true&w=majority")
    client.admin.command('ping')
    print("✅ Connected successfully to MongoDB!")
except Exception as e:
    print("❌ Connection failed:", e)

from flask import Flask, render_template, request
from pymongo import MongoClient

app = Flask(__name__)


client = MongoClient("mongodb+srv://deysudeep81_db_user:oxKsEDRTjjrqVzWA@flasktudedude.m9pktx3.mongodb.net/")
db = client["flasktutedude"]        # database
collection = db["form_data"]        # collection


@app.route('/')
def home():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    email = request.form['email']

 
    if name == "" or email == "":
        return "Please fill all fields!"

   
    collection.insert_one({"name": name, "email": email})

    return "Data submitted successfully!"


if __name__ == '__main__':
    app.run(debug=True)

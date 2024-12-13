import os
import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for
from google.cloud.sql.connector import Connector
import sqlalchemy
from google.cloud import pubsub_v1
import json

app = Flask(__name__)

# Configuration for Cloud SQL instance
instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME", "cload-app-dev-final:asia-northeast1:event-management-system-db-1")
db_user = os.environ.get("DB_USER", "root1")
db_pass = os.environ.get("DB_PASS", "password1")
db_name = os.environ.get("DB_NAME", "event_mgmt")

# Initialize the Cloud SQL Python Connector object
connector = Connector()

# Initialize Pub/Sub Publisher
project_id = 'cload-app-dev-final'
publisher = pubsub_v1.PublisherClient()
participant_topic = publisher.topic_path(project_id, 'participant-registrations')
notification_topic = publisher.topic_path(project_id, 'event-notifications')

# Function to publish messages to Pub/Sub
def publish_message(topic, message_data):
    message_json = json.dumps(message_data).encode('utf-8')
    future = publisher.publish(topic, message_json)
    print(f'Published message to {topic}: {message_data}')
    return future.result()

# Function to create a connection to the database
def getconn():
    conn = connector.connect(
        instance_connection_name,
        "pymysql",
        user=db_user,
        password=db_pass,
        db=db_name,
    )
    return conn

# Create connection pool
pool = sqlalchemy.create_engine(
    "mysql+pymysql://",
    creator=getconn,
)

def runQuery(query):
    try:
        with pool.connect() as db_conn:
            print("Connected to Cloud SQL, running query: ", query)
            result = db_conn.execute(sqlalchemy.text(query))
            db_conn.commit()
            try:
                rows = result.fetchall()
                if rows:
                    if isinstance(rows[0], dict):
                        return rows
                    else:
                        return [dict(zip(result.keys(), row)) for row in rows]
                else:
                    return []
            except Exception as e:
                print("Query returned nothing or encountered an error: ", e)
                return []
    except Exception as e:
        print("Error executing query: ", e)
        return []

@app.route('/', methods=['GET', 'POST'])
def renderLoginPage():
    events = runQuery("SELECT * FROM events")
    branch =  runQuery("SELECT * FROM branch")
    if request.method == 'POST':
        Name = request.form['FirstName'] + " " + request.form['LastName']
        Mobile = request.form['MobileNumber']
        Branch_id = request.form['Branch']
        Event = request.form['Event']
        Email = request.form['Email']

        if len(Mobile) != 10:
            return render_template('loginfail.html',errors = ["Invalid Mobile Number!"])

        if Email[-4:] != '.com':
            return render_template('loginfail.html', errors = ["Invalid Email!"])

        if len(runQuery("SELECT * FROM participants WHERE event_id={} AND mobile={}".format(Event,Mobile))) > 0 :
            return render_template('loginfail.html', errors = ["Student already Registered for the Event!"])

        if runQuery("SELECT COUNT(*) FROM participants WHERE event_id={}".format(Event)) >= runQuery("SELECT participants FROM events WHERE event_id={}".format(Event)):
            return render_template('loginfail.html', errors = ["Participants count fullfilled Already!"])

        runQuery("INSERT INTO participants(event_id,fullname,email,mobile,college,branch_id) VALUES({},\"{}\",\"{}\",\"{}\",\"COEP\",\"{}\");".format(Event,Name,Email,Mobile,Branch_id))

        # Publish registration event to Pub/Sub
        registration_data = {
            "participantId": Name,
            "eventId": Event,
            "name": Name,
            "email": Email,
            "mobile": Mobile
        }
        publish_message(participant_topic, registration_data)

        return render_template('index.html',events = events,branchs = branch,errors=["Succesfully Registered!"])

    return render_template('index.html',events = events,branchs = branch)

@app.route('/loginfail', methods=['GET'])
def renderLoginFail():
    return render_template('loginfail.html')

@app.route('/admin', methods=['GET', 'POST'])
def renderAdmin():
    if request.method == 'POST':
        UN = request.form['username']
        PS = request.form['password']

        cred = runQuery("SELECT * FROM admin")
        print(cred)
        for user in cred:
            if UN == user['username'] and PS == user['password']:
                return redirect('/eventType')

        return render_template('admin.html', errors=["Wrong Username/Password"])

    return render_template('admin.html')

@app.route('/eventType', methods=['GET', 'POST'])
def getEvents():
    eventTypes = runQuery("SELECT *,(SELECT COUNT(*) FROM participants AS P WHERE T.type_id IN (SELECT type_id FROM events AS E WHERE E.event_id = P.event_id ) ) AS COUNT FROM event_type AS T;")
    print(eventTypes)

    events = runQuery("SELECT event_id,event_title,(SELECT COUNT(*) FROM participants AS P WHERE P.event_id = E.event_id ) AS count FROM events AS E;")
    print(events)

    types = runQuery("SELECT * FROM event_type;")
    print(types)

    location = runQuery("SELECT * FROM location;")
    print(location)

    if request.method == "POST":
        try:
            Name = request.form["newEvent"]
            fee=request.form["Fee"]
            participants = request.form["maxP"]
            Type=request.form["EventType"]
            Location = request.form["EventLocation"]
            Date = request.form['Date']
            runQuery("INSERT INTO events(event_title,event_price,participants,type_id,location_id,date) VALUES(\"{}\",{},{},{},{},\'{}\');".format(Name,fee,participants,Type, Location,Date))

        except:
            EventId=request.form["EventId"]
            runQuery("DELETE FROM events WHERE event_id={}".format(EventId))

    return render_template('events.html',events = events,eventTypes = eventTypes,types = types,locations = location)

@app.route('/eventinfo')
def rendereventinfo():
    events=runQuery("SELECT *,(SELECT COUNT(*) FROM participants AS P WHERE P.event_id = E.event_id ) AS count FROM events AS E LEFT JOIN event_type USING(type_id) LEFT JOIN location USING(location_id);")

    return render_template('events_info.html',events = events)

@app.route('/participants', methods=['GET', 'POST'])
def renderParticipants():

    events = runQuery("SELECT * FROM events;")

    if request.method == "POST":
        Event = request.form['Event']

        participants = runQuery("SELECT p_id,fullname,mobile,email FROM participants WHERE event_id={}".format(Event))
        return render_template('participants.html',events = events,participants=participants)

    return render_template('participants.html',events = events)

@app.route('/sendNotification', methods=['POST'])
def sendEventNotification():
    if request.method == 'POST':
        Event = request.form['Event']
        notification_message = request.form['NotificationMessage']

        # Example: Publish notification event to Pub/Sub
        notification_data = {
            "eventId": Event,
            "message": notification_message
        }
        publish_message(notification_topic, notification_data)

        return render_template('admin.html', errors=["Notification sent successfully!"])

    return render_template('admin.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
## Subscriber for Registration Events:
```python
from google.cloud import pubsub_v1
import json

# Initialize Pub/Sub Subscriber
subscriber = pubsub_v1.SubscriberClient()
participant_subscription = subscriber.subscription_path('your-gcp-project-id', 'db-updater-sub')

def callback(message):
    data = json.loads(message.data)
    print(f"Processing registration for {data['name']} in event {data['eventId']}")
    message.ack()
# Listen for incoming registration events
subscriber.subscribe(participant_subscription, callback=callback)
```

## Subscriber for Notification Events:
```python
def notification_callback(message):
   data = json.loads(message.data)
   print(f"Sending notification for Event {data['eventId']}: {data['message']}")
   # Example: Send email or SMS
   message.ack()

# Listen for notification events
subscriber.subscribe('your-gcp-project-id', 'notification-sender-sub', callback=notification_callback)
```
## Integration
###   Publishers (Flask routes) send events to Pub/Sub when a participant registers or when an event notification needs to be sent.
###   Subscribers (Python scripts) listen for these events and handle them accordingly (e.g., database updates, sending emails/SMS).
from google.cloud import pubsub_v1
import json

# Initialize Pub/Sub Subscriber
subscriber = pubsub_v1.SubscriberClient()
participant_subscription = subscriber.subscription_path('cload-app-dev-final', 'db-updater-sub')

def notification_callback(message):
    data = json.loads(message.data)
    print(f"Sending notification for Event {data['eventId']}: {data['message']}")
    # Example: Send email or SMS
    message.ack()

# Listen for notification events
subscriber.subscribe('cload-app-dev-final', 'notification-sender-sub', callback=notification_callback)

const { PubSub } = require('@google-cloud/pubsub');
const pubsub = new PubSub();

async function publishRegistrationEvent(eventData) {
    const topicName = 'participant-registrations';
    const messageBuffer = Buffer.from(JSON.stringify(eventData));

    await pubsub.topic(topicName).publish(messageBuffer);
    console.log(`Registration event published: ${JSON.stringify(eventData)}`);
}

// Example Usage
publishRegistrationEvent({
    participantId: 101,
    eventId: 1,
    name: 'Alice Johnson',
    email: 'alice@example.com',
    mobile: '1234567890',
});

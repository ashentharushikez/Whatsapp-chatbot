import fetch from 'node-fetch';
import pkg from 'whatsapp-web.js';
const { Client, LocalAuth, MessageMedia } = pkg;
import qrcode from 'qrcode-terminal';
import amqp from 'amqplib';
import fs from 'fs';
import path from 'path';

// Add MIME type mapping
const MIME_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif'
};

const API_URL = process.env.API_URL || 'http://python-api:5000';

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ],
        executablePath: '/usr/bin/chromium'
    }
});

client.on('message', async msg => {
    try {
        if (msg.from === 'status@broadcast' || !msg.body) {
            return;
        }

        const response = await fetch('http://python-api:5000/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                number: msg.from,
                message: msg.body
            })
        });

        const data = await response.json();

        if (data.success) {
            if (data.image) {
                try {
                    // Log the image URL for debugging
                    console.log('Attempting to fetch image from:', data.image);
                    
                    // Use the correct path format
                    const imageUrl = data.image.startsWith('http') 
                        ? data.image 
                        : `http://python-api:5000/static/image${data.image}`;

                    console.log('Full image URL:', imageUrl);

                    const imageResponse = await fetch(imageUrl);
                    if (!imageResponse.ok) {
                        throw new Error(`Failed to fetch image: ${imageResponse.statusText} (${imageUrl})`);
                    }

                    const buffer = await imageResponse.buffer();
                    const media = new MessageMedia(
                        'image/jpeg',
                        buffer.toString('base64'),
                        'shop_image.jpg'
                    );

                    await client.sendMessage(msg.from, media, {
                        caption: data.response || data.text
                    });
                } catch (imageError) {
                    console.error('Error fetching/sending image:', imageError);
                    await client.sendMessage(msg.from, data.response || data.text);
                }
            } else {
                await client.sendMessage(msg.from, data.response || data.text);
            }
        }
    } catch (error) {
        console.error('Error in message handler:', error);
    }
});


// QR Code handling
client.on('qr', (qr) => {
    console.log('New QR Code received:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('WhatsApp client is ready!');
    connectQueue();
});


client.on('auth_failure', msg => {
    console.error('Authentication failed:', msg);
});

client.on('disconnected', (reason) => {
    console.log('Client disconnected:', reason);
});

async function connectQueue() {
    try {
        const connection = await amqp.connect('amqp://rabbitmq');
        const channel = await connection.createChannel();
        const queue = 'whatsapp_messages';

        await channel.assertQueue(queue, { durable: true });
        console.log('Connected to RabbitMQ, waiting for messages...');

        channel.consume(queue, async (msg) => {
            if (msg !== null) {
                try {
                    const data = JSON.parse(msg.content.toString());
                    const chatId = `${data.number}@c.us`;
                    
                    console.log('Sending WhatsApp message:', {
                        to: chatId,
                        message: data.message
                    });

                    await client.sendMessage(chatId, data.message);
                    channel.ack(msg);
                    
                } catch (error) {
                    console.error('Error processing RabbitMQ message:', error);
                    channel.nack(msg);
                }
            }
        });

    } catch (error) {
        console.error('RabbitMQ connection error:', error);
        setTimeout(connectQueue, 5000);
    }
}

client.initialize().catch(err => {
    console.error('Client initialization failed:', err);
});
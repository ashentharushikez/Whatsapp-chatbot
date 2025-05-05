import fetch from 'node-fetch';
import pkg from 'whatsapp-web.js';
const { Client, LocalAuth, MessageMedia } = pkg;
import qrcode from 'qrcode-terminal';
import amqp from 'amqplib';
import fs from 'fs';
import path from 'path';


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
        // Ignore status broadcasts and empty messages
        if (msg.from === 'status@broadcast' || !msg.body) {
            return;
        }

        console.log('Received WhatsApp message:', {
            from: msg.from,
            body: msg.body
        });

        // Send message to Python API
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
        console.log('Python API response:', data);

        if (data.success) {
            // Handle text response
            await msg.reply(data.response);

            // Handle image if present
            if (data.image) {
                try {
                    const media = await MessageMedia.fromUrl(data.image);
                    await msg.reply(media);
                } catch (imageError) {
                    console.error('Error sending image:', imageError);
                }
            }
        } else {
            console.error('API Error:', data.error);
        }
    } catch (error) {
        console.error('Error processing message:', error);
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
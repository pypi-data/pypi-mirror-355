from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage, ServiceBusReceiveMode
from azure.servicebus.exceptions import ServiceBusError
import json
from typing import Optional
from ..logger import setup_logger

logger = setup_logger(__name__)

class AzureServiceBus:
    def __init__(self, connection_string: str, queue_name: str):
        self.connection_string = connection_string
        self.queue_name = queue_name
        self.client = ServiceBusClient.from_connection_string(conn_str=connection_string)
        self.sender = None
        self.receiver = None

    async def connect(self):
        """Establish sender and receiver clients"""
        try:
            self.sender = self.client.get_queue_sender(queue_name=self.queue_name)
            self.receiver = self.client.get_queue_receiver(
                queue_name=self.queue_name,
                receive_mode=ServiceBusReceiveMode.PEEK_LOCK
            )
            logger.info(f"Connected to queue: {self.queue_name}")
        except ServiceBusError as e:
            logger.error(f"Connection error: {e}")
            raise

    async def disconnect(self):
        """Close connections"""
        try:
            if self.sender:
                await self.sender.close()
            if self.receiver:
                await self.receiver.close()
            await self.client.close()
            logger.info("Disconnected from Service Bus")
        except ServiceBusError as e:
            logger.error(f"Disconnection error: {e}")
            raise

    async def send(self, event_payload: dict):
        """Send a message to the queue"""
        if not self.sender:
            await self.connect()
        try:
            message = ServiceBusMessage(
                body=json.dumps(event_payload),
                content_type="application/json"
            )
            await self.sender.send_messages(message)
            logger.info("Message sent")
        except ServiceBusError as e:
            logger.error(f"Send error: {e}")
            raise

    async def receive_messages(self, max_message_count: int = 1, timeout: int = 30):
        """Receive messages from the queue"""
        if not self.receiver:
            await self.connect()
        try:
            return await self.receiver.receive_messages(
                max_message_count=max_message_count,
                max_wait_time=timeout
            )
        except ServiceBusError as e:
            logger.error(f"Receive error: {e}")
            raise

    async def complete_message(self, message):
        """Mark a received message as completed"""
        try:
            await self.receiver.complete_message(message)
            logger.info("Message completed")
        except ServiceBusError as e:
            logger.error(f"Completion error: {e}")
            raise

import requests
import json


class WebhookSender:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Implementation of the Singleton pattern.
        Returns the existing instance if it exists, otherwise creates a new one.
        """
        if cls._instance is None:
            cls._instance = super(WebhookSender, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, endpoint_url=None):
        """
        Initialize the WebhookSender with the target endpoint URL.
        Endpoint URL is required only on first initialization.

        Args:
            endpoint_url (str, optional): The URL where the webhook will be sent.
                                         Required only for first initialization.
        """
        if not getattr(self, '_initialized', False):
            if endpoint_url is None:
                raise ValueError("endpoint_url is required for first initialization")
            self.endpoint_url = endpoint_url
            self._initialized = True
            print(f"Webhook Sender Initialised: {endpoint_url}")
        elif endpoint_url is not None:
            print("Warning: WebhookSender is already initialized. Ignoring new endpoint URL.")

    def send_webhook(self, peer_id, audio_file_url):
        """
        Send a webhook with the specified peer ID and audio file URL.

        Args:
            peer_id (str): The peer ID to include in the payload
            audio_file_url (str): The URL of the audio file

        Returns:
            requests.Response: The response from the webhook endpoint

        Raises:
            requests.exceptions.RequestException: If the request fails
        """
        payload = {
            "peerId": peer_id,
            "audioFile": audio_file_url
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                url=self.endpoint_url,
                data=json.dumps(payload),
                headers=headers,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            raise e

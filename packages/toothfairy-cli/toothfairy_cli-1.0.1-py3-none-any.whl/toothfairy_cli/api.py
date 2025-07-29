import os
import requests
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ToothFairyAPI:
    def __init__(self, base_url: str, ai_url: str, api_key: str, workspaceid: str, verbose: bool = False):
        """
        Initialize the ToothFairyAPI client.

        Args:
            base_url (str): The base URL for the ToothFairy API.
            ai_url (str): The URL for AI-related endpoints.
            api_key (str): The API key for authentication.
            workspaceid (str): The workspaceid for authentication.
            verbose (bool): Enable verbose logging for debugging.
        """
        self.base_url = base_url
        self.ai_url = ai_url
        self.workspaceid = workspaceid
        self.verbose = verbose
        self.headers = {"Content-Type": "application/json", "x-api-key": api_key}

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a request to the ToothFairy API.

        Args:
            method (str): The HTTP method to use.
            endpoint (str): The API endpoint to call.
            data (dict, optional): The data to send with the request.

        Returns:
            dict: The JSON response from the API.

        Raises:
            requests.HTTPError: If the request fails.
        """
        if method in ["POST", "PUT"] and data:
            data = {"workspaceid": self.workspaceid, **data}
        elif method == "GET" and data:
            # For GET requests, add data as query parameters
            from urllib.parse import urlencode
            query_params = urlencode(data)
            endpoint = f"{endpoint}?{query_params}"
            
        url = f"{self.base_url}/{endpoint}"
        
        if self.verbose:
            from rich.console import Console
            console = Console()
            console.print(f"[dim]--- API Request Debug ---[/dim]", err=True)
            console.print(f"[dim]Method: {method}[/dim]", err=True)
            console.print(f"[dim]URL: {url}[/dim]", err=True)
            console.print(f"[dim]Headers: {self.headers}[/dim]", err=True)
            if data and method in ["POST", "PUT"]:
                console.print(f"[dim]Data: {data}[/dim]", err=True)
            console.print(f"[dim]----------------------[/dim]", err=True)
        
        try:
            response = requests.request(method, url, headers=self.headers, json=data if method in ["POST", "PUT"] else None)
            
            if self.verbose:
                from rich.console import Console
                console = Console()
                console.print(f"[dim]--- API Response Debug ---[/dim]", err=True)
                console.print(f"[dim]Status: {response.status_code} {response.reason}[/dim]", err=True)
                console.print(f"[dim]Response Headers: {dict(response.headers)}[/dim]", err=True)
                console.print(f"[dim]Response Data: {response.text}[/dim]", err=True)
                console.print(f"[dim]------------------------[/dim]", err=True)
            
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            if self.verbose:
                from rich.console import Console
                console = Console()
                console.print(f"[red]--- API Error Debug ---[/red]", err=True)
                console.print(f"[red]HTTP Error: {http_err}[/red]", err=True)
                console.print(f"[red]Status: {response.status_code}[/red]", err=True)
                console.print(f"[red]Response: {response.text}[/red]", err=True)
                console.print(f"[red]---------------------[/red]", err=True)
            logger.error(f"HTTP error occurred: {http_err}")
            raise
        except Exception as err:
            if self.verbose:
                from rich.console import Console
                console = Console()
                console.print(f"[red]--- API Error Debug ---[/red]", err=True)
                console.print(f"[red]Error: {err}[/red]", err=True)
                console.print(f"[red]---------------------[/red]", err=True)
            logger.error(f"An error occurred: {err}")
            raise

    def create_chat(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new chat."""
        return self._make_request("POST", "chat/create", chat_data)

    def update_chat(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing chat."""
        return self._make_request("POST", "chat/update", chat_data)

    def get_chat(self, chat_id: str) -> Dict[str, Any]:
        """Get a chat by its ID."""
        return self._make_request("GET", f"chat/get/{chat_id}?workspaceid={self.workspaceid}")

    def create_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new message in a chat."""
        return self._make_request("POST", "chat_message/create", message_data)

    def get_message(self, message_id: str) -> Dict[str, Any]:
        """Get a message by its ID."""
        return self._make_request("GET", f"chat_message/get/{message_id}")

    def get_all_chats(self) -> Dict[str, Any]:
        """Get all chats for the workspace."""
        return self._make_request(
            "GET", f"chat/list?workspaceid={self.workspaceid}"
        )

    def get_agent_response(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a response from an AI agent.

        Args:
            agent_data (dict): The data for the agent request.

        Returns:
            dict: The agent's response data.

        Raises:
            requests.HTTPError: If the request fails.
        """
        url = f"{self.ai_url}/chatter"
        agent_data = {"workspaceid": self.workspaceid, **agent_data}
        try:
            response = requests.post(url, headers=self.headers, json=agent_data)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            raise
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            raise

    def send_message_to_agent(
        self,
        message: str,
        agent_id: str,
        phone_number: Optional[str] = None,
        customer_id: Optional[str] = None,
        provider_id: Optional[str] = None,
        customer_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to an agent and get a response.
        
        This combines chat creation, message creation, and agent response.
        """
        if customer_info is None:
            customer_info = {}

        try:
            # Use defaults for optional parameters
            customer_id = customer_id or f"cli-user-{hash(message) % 10000}"
            phone_number = phone_number or "+1234567890"
            provider_id = provider_id or "default-sms-provider"
            
            chat_data = {
                "name": customer_id,
                "primaryRole": agent_id,
                "externalParticipantId": phone_number,
                "channelSettings": {
                    "sms": {
                        "isEnabled": True,
                        "recipient": phone_number,
                        "providerID": provider_id,
                    }
                },
                "customerId": customer_id,
                "customerInfo": customer_info,
                "isAIReplying": True,
            }

            created_chat = self.create_chat(chat_data)
            logger.debug(f"Chat created: {created_chat['id']}")

            message_data = {
                "chatID": created_chat["id"],
                "text": message,
                "role": "user",
                "userID": "CLI",
            }
            created_message = self.create_message(message_data)
            logger.debug(f"Message created: {created_message['id']}")

            agent_data = {
                "chatid": created_chat["id"],
                "messages": [
                    {
                        "text": created_message["text"],
                        "role": created_message["role"],
                        "userID": created_message.get("userID", "System User"),
                    }
                ],
                "agentid": agent_id,
            }
            agent_response = self.get_agent_response(agent_data)
            logger.debug("Agent response received")
            
            return {
                "chat_id": created_chat["id"],
                "message_id": created_message["id"],
                "agent_response": agent_response
            }
        except Exception as e:
            logger.error(f"Error in send_message_to_agent: {e}")
            raise

    def search_documents(
        self,
        text: str,
        top_k: int = 10,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for documents in the knowledge hub.
        
        Args:
            text (str): Search query text
            top_k (int): Number of documents to retrieve (1-50)
            metadata (dict, optional): Metadata filters for advanced search
                - status: Document status filter ("published" or "suspended")
                - documentId: Specific document ID to search within
                - topic: Array of topic IDs to filter by
        
        Returns:
            dict: Search results with relevant documents
        """
        if not 1 <= top_k <= 50:
            raise ValueError("top_k must be between 1 and 50")
        
        search_data = {
            "text": text,
            "topK": top_k
        }
        
        if metadata:
            search_data["metadata"] = metadata
        
        url = f"{self.ai_url}/searcher"
        search_data = {"workspaceid": self.workspaceid, **search_data}
        
        try:
            response = requests.post(url, headers=self.headers, json=search_data)
            response.raise_for_status()
            return response.json()
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred during search: {http_err}")
            raise
        except Exception as err:
            logger.error(f"An error occurred during search: {err}")
            raise
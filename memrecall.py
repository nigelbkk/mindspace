"""
Title: Memory Filter
Author: Your Name
Version: 1.0.0
Required Open WebUI Version: 0.3.0
"""

import logging

import requests
import json
from typing import Optional, Callable, Awaitable
from pydantic import BaseModel, Field


class Filter:
    class Valves(BaseModel):
        priority: int = 0
        backend_url: str = Field(default="http://localhost:8000")

    def __init__(self):
        self.valves = self.Valves()

    def _call_backend(self, endpoint: str, content: str) -> dict:
        """Call backend API"""
        url = f"{self.valves.backend_url}/{endpoint}"
        logging.info(url)
        headers = {"Content-Type": "application/json"}

        payload = {
            "role": "system",
            "text": content,
            "type": "user_note",
            "importance": 5,
            "tags": [self.user_id, "explicit"],
        }
        response = requests.post(url, json=payload, headers=headers or {}, timeout=10)
        logging.info(response.status_code)
        return response

    def _remember(self, content):
        logging.info("_remember")
        return self._call_backend("/memory/remember", content)

    def _inject_static_context(self, messages):
        logging.info("_inject_static_context")
        response = self._call_backend("memory/context", {"user_id": self.user_id})

        o = json.loads(response.text)
        context = o["context"]
        # logging.info(o["context"])
        if context:
            messages.insert(-1, {"role": "system", "content": context})
            return context

    def _semantic_recall(self, last_message):
        try:
            logging.info("semantic_recall")
            logging.info(last_message)
            response = self._call_backend("/memory/recall", last_message)
            logging.info(response.text)

            if response.status_code == 200:
                memories = response.json().get("matches", [])
                logging.info(memories[0])
                return memories

        except requests.exceptions.RequestException as e:
            pass

    async def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        messages = body.get("messages", [])
        if not messages:
            return body

        self.user_id = __user__.get("id") if __user__ else "unknown"
        self.user_name = __user__.get("name") if __user__ else "anonymous"
        user_message = messages[-1].get("content", "")
        logging.info(user_message)
        logging.info(self.user_id)

        # Check for explicit commands
        if user_message.lower().startswith("remember "):
            text_to_remember = user_message[8:].strip()
            result = self._remember(text_to_remember)
            messages[-1]["content"] = result.text
            body["messages"] = messages
            return body

        if user_message.lower().startswith("forget "):
            return body
        if user_message.lower().startswith("recall "):
            return body

        # context = self._inject_static_context(messages)

        # Get context for regular queries
        memories = self._semantic_recall(user_message)
        logging.info(f"memories: {memories}")
        if not memories:
            print("No memories found")
            return body

        # prepend retrieved memories to conversation
        memories_json = json.dumps(memories, indent=2)
        body["messages"].insert(
            0,
            {
                "role": "system",
                "content": f"Relevant memories about this user:\n{memories_json}",
            },
        )
        return body

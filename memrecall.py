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

logging.info("===== MEMRECALL LOADED ==========")


class Filter:
    logging.info("===== MEMRECALL Filter LOADED ==========")

    class Valves(BaseModel):
        priority: int = 0
        backend_url: str = Field(default="http://localhost:8000")

    def __init__(self):
        self.valves = self.Valves()

    def _call_backend(self, endpoint: str, data: dict) -> dict:
        """Call backend API"""
        url = f"{self.valves.backend_url}/{endpoint}"
        logging.info(url)
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers or {}, timeout=10)
        logging.info(response.status_code)

        return response

    def _semantic_recall(self, last_message):
        try:
            logging.info("semantic_recall")

            payload = {
                "query": last_message,  # send the user message
                "tags": [self.user_id],  # restrict to this user
                "k": 5,  # number of memories to retrieve
            }
            logging.info(last_message)
            response = self._call_backend("/memory/recall", payload)
            # logging.info(response.text)

            if response.status_code == 200:
                memories = response.json().get("matches", [])
                logging.info(memories[0])
                return memories

        except requests.exceptions.RequestException as e:
            pass

    async def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        logging.info("=== INLET FILTER CALLED ===")

        # self.user_id = __user__.get("id") if __user__ else "anonymous"
        messages = body.get("messages", [])
        if not messages:
            return body

        user_message = messages[-1].get("content", "")
        logging.info(user_message)
        self.user_id = __user__.get("id") if __user__ else "anonymous"
        logging.info(self.user_id)

        # Check for explicit commands
        if user_message.lower().startswith("/memory/remember "):
            text_to_remember = user_message[8:].strip()
            result = self._call_backend(
                "remember",
                {
                    "text": text_to_remember,
                    "type": "user_note",
                    "importance": 5,
                    "tags": [self.user_id, "explicit"],
                },
            )

            logging.info(result)
            messages[-1]["content"] = result.get("response", "Remembered")
            body["messages"] = messages

        if user_message.lower().startswith("forget "):
            result = await self._call_backend("forget", {"message": user_message})
            messages[-1]["content"] = result.get("response", "Forgotten")
            body["messages"] = messages

        if user_message.lower().startswith("recall "):
            result = await self._call_backend("recall", {"message": user_message})
            if result.get("context"):
                messages.insert(-1, {"role": "system", "content": result["context"]})
            body["messages"] = messages

        # Get context for regular queries
        # result = await self._call_backend("context", {"query": user_message})

        # if result.get("context"):
        #    messages.insert(-1, {"role": "system", "content": result["context"]})

        memories = self._semantic_recall(user_message)
        logging.info(f"memories: {memories}")
        if memories:
            # prepend retrieved memories to conversation
            logging.info(f"memories: {memories}")
            logging.info(f"body: {body}")
            logging.info(type(body["messages"]))
            logging.info(type(memories))

            logging.info(f"TYPE OF messages: {type(body['messages'])}")
            logging.info(f"TYPE OF memories: {type(memories)}")
            logging.info(f"ABOUT TO INSERT")

            memories_json = json.dumps(memories, indent=2)

            body["messages"].insert(
                0,
                {
                    "role": "system",
                    "content": f"Relevant memories about this user:\n{memories_json}",
                },
            )
            logging.info("AFTER INSERT")

            logging.info(f"body: {body}")
        return body


"""
Backend API needs these endpoints:

POST /remember
{"message": "remember the WG is 'awooga' on 123.324.57.152"}
→ {"response": "✓ Remembered: awooga"}

POST /forget  
{"message": "forget awooga"}
→ {"response": "✓ Forgotten: awooga"}

POST /recall
{"message": "recall awooga"}
→ {"context": "awooga: WireGuard at 123.324.57.152"}

POST /context
{"query": "check if awooga is responding"}
→ {"context": "[CONTEXT]\nLocation: Thailand\n[SYSTEMS]\nawooga: ..."}
"""

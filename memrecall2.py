"""
title: Memory Recall Filter
author: Nigel
version: 0.1
"""

from pydantic import BaseModel, Field
from typing import Optional
import requests
import json


class Filter:
    class Valves(BaseModel):
        BACKEND_URL: str = Field(
            default="http://127.0.0.1:8000",
            # default="http://10.0.0.2:8000",
            description="URL of your Python backend service",
        )
        API_KEY: str = Field(
            default="", description="API key for authentication (if needed)"
        )

    def __init__(self):
        self.valves = self.Valves()

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """
        Pre-process chat messages: handle remember, recall, forget
        """
        messages = body.get("messages", [])
        if not messages:
            return body

        user_id = __user__.get("id") if __user__ else "anonymous"
        last_message = messages[-1].get("content", "")

        headers = {"Content-Type": "application/json"}
        if self.valves.API_KEY:
            headers["Authorization"] = f"Bearer {self.valves.API_KEY}"

        try:
            # REMEMBER
            if last_message.lower().startswith("remember"):
                text_to_remember = last_message[8:].strip()
                requests.post(
                    f"{self.valves.BACKEND_URL}/memory/remember",
                    json={
                        "text": text_to_remember,
                        "type": "user_note",
                        "importance": 5,
                        "tags": [user_id, "explicit"],
                    },
                    headers=headers,
                    timeout=10,
                )

            # FORGET
            elif last_message.lower().startswith("forget"):
                requests.post(
                    f"{self.valves.BACKEND_URL}/memory/forget",
                    json={"text": last_message, "user_id": user_id},
                    headers=headers,
                    timeout=10,
                )

        except requests.exceptions.RequestException:
            pass  # silently ignore network errors

        # --- AUTOMATIC SEMANTIC RECALL ---
        # This is the only new addition. We send every user message to recall endpoint.
        try:

            recall_payload = {
                "query": last_message,  # send the user message
                # "tags": [user_id],  # restrict to this user
                "k": 5,  # number of memories to retrieve
            }

            recall_response = requests.post(
                f"{self.valves.BACKEND_URL}/memory/recall",
                json=recall_payload,
                headers=headers,
                timeout=10,
            )

            if recall_response.status_code == 200:
                memories = recall_response.json().get("memories", [])
                if memories:
                    # prepend retrieved memories to conversation
                    body["messages"].insert(
                        0,
                        {
                            "role": "system",
                            "content": f"Relevant memories about this user:\n{json.dumps(memories, indent=2)}",
                        },
                    )

        except requests.exceptions.RequestException as e:
            print(f"[Memory Plugin] Recall network error: {e}")

        return body

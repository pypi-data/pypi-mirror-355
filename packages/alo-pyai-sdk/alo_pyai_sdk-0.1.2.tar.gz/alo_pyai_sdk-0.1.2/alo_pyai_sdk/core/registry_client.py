from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, HttpUrl

# --- Models for Registry Interaction (mirroring registry's expected models) ---

class RegisteredAgentInfo(BaseModel):
    service_id: str
    service_url: HttpUrl # Correctly using HttpUrl
    # Add other relevant fields like skills, description, llm_config_name, etc.
    # that the registry might store and expose.
    last_seen: Optional[str] = None # Example: ISO datetime string

class AgentRegistrationPayload(BaseModel):
    service_id: str
    service_url: HttpUrl # Correctly using HttpUrl
    # skills: List[str] = [] # Example
    # description: Optional[str] = None # Example

# --- Registry Client ---

class RegistryClient:
    def __init__(self, registry_base_url: str):
        self.base_url = registry_base_url.rstrip('/')
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def list_agents(self) -> List[RegisteredAgentInfo]:
        """Fetches the list of registered agents from the registry."""
        try:
            response = await self.client.get("/agents")
            response.raise_for_status() # Raise an exception for bad status codes
            return [RegisteredAgentInfo(**agent_data) for agent_data in response.json()]
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred while listing agents: {e.response.status_code} - {e.response.text}")
            return []
        except httpx.RequestError as e:
            print(f"Request error occurred while listing agents: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

    async def register_agent(self, payload: AgentRegistrationPayload) -> bool:
        """Registers an agent with the registry."""
        try:
            response = await self.client.post("/register", json=payload.model_dump())
            response.raise_for_status()
            # Assuming registry returns 200 or 201 on successful registration
            print(f"Agent '{payload.service_id}' registered successfully with registry at {self.base_url}.")
            return True
        except httpx.HTTPStatusError as e:
            print(f"HTTP error registering agent '{payload.service_id}': {e.response.status_code} - {e.response.text}")
            return False
        except httpx.RequestError as e:
            print(f"Request error registering agent '{payload.service_id}': {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during registration: {e}")
            return False

    async def unregister_agent(self, service_id: str) -> bool:
        """Unregisters an agent from the registry."""
        try:
            # Assuming unregister might take service_id in payload or path
            # For this example, let's assume it's in the payload for consistency
            response = await self.client.post("/unregister", json={"service_id": service_id})
            response.raise_for_status()
            print(f"Agent '{service_id}' unregistered successfully.")
            return True
        except httpx.HTTPStatusError as e:
            print(f"HTTP error unregistering agent '{service_id}': {e.response.status_code} - {e.response.text}")
            return False
        except httpx.RequestError as e:
            print(f"Request error unregistering agent '{service_id}': {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred during unregistration: {e}")
            return False

    async def close(self):
        await self.client.aclose()

async def main_test():
    # This is for testing the client directly.
    # Assumes a registry server is running at http://localhost:8000
    
    # First, ensure you have a dummy registry running.
    # You can create a simple one with FastAPI for testing:
    # from fastapi import FastAPI, HTTPException
    # app_test_registry = FastAPI()
    # agents_db = {}
    # @app_test_registry.post("/register")
    # async def _register(payload: AgentRegistrationPayload): agents_db[payload.service_id] = payload; return payload
    # @app_test_registry.get("/agents")
    # async def _list_agents(): return list(agents_db.values())
    # # Run this with: uvicorn your_test_registry_file:app_test_registry --port 8000
    
    client = RegistryClient("http://localhost:8000")
    
    print("--- Listing agents (initially) ---")
    agents = await client.list_agents()
    if not agents:
        print("No agents found.")
    else:
        for agent in agents:
            print(agent)
            
    print("\n--- Registering agent 'test_agent_001' ---")
    reg_payload = AgentRegistrationPayload(service_id="test_agent_001", service_url="http://localhost:8001")
    success = await client.register_agent(reg_payload)
    print(f"Registration successful: {success}")

    print("\n--- Listing agents (after registration) ---")
    agents = await client.list_agents()
    for agent in agents:
        print(agent)

    # print("\n--- Unregistering agent 'test_agent_001' ---")
    # success = await client.unregister_agent("test_agent_001")
    # print(f"Unregistration successful: {success}")

    # print("\n--- Listing agents (after unregistration) ---")
    # agents = await client.list_agents()
    # if not agents:
    #     print("No agents found.")
    # else:
    #     for agent in agents:
    #         print(agent)
            
    await client.close()

if __name__ == "__main__":
    import asyncio
    # To run this test, you need a dummy FastAPI registry server running on port 8000.
    # See comments in main_test() for a simple example.
    # asyncio.run(main_test())
    print("RegistryClient defined. Run with a test registry server to see it in action.")

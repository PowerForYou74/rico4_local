#!/usr/bin/env python3
"""
n8n Auto-Bootstrap: Upsert & Activate Workflow
Importiert/aktualisiert den Rico V5 Event Hub Workflow automatisch
"""
import os
import json
import sys
import asyncio
import httpx
from typing import Dict, Any, Optional
from pathlib import Path

# ENV-Konfiguration laden
N8N_ENABLED = os.getenv("N8N_ENABLED", "false").lower() == "true"
N8N_HOST = os.getenv("N8N_HOST", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY")
N8N_TIMEOUT_SECONDS = int(os.getenv("N8N_TIMEOUT_SECONDS", "15"))

# Workflow-Konfiguration
WORKFLOW_NAME = "Rico V5 – Event Hub"
WORKFLOW_JSON_PATH = Path(__file__).parent / "workflows" / "rico_v5_event_hub.json"

class N8NBootstrap:
    def __init__(self):
        self.client = None
        self.headers = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = httpx.Timeout(N8N_TIMEOUT_SECONDS)
        self.client = httpx.AsyncClient(timeout=timeout)
        
        # Headers setzen
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        if N8N_API_KEY:
            self.headers["X-N8N-API-KEY"] = N8N_API_KEY
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.client:
            await self.client.aclose()
    
    def load_workflow_json(self) -> Dict[str, Any]:
        """Lädt den Workflow-JSON aus der Datei"""
        if not WORKFLOW_JSON_PATH.exists():
            raise FileNotFoundError(f"Workflow JSON not found: {WORKFLOW_JSON_PATH}")
        
        with open(WORKFLOW_JSON_PATH, 'r') as f:
            workflow = json.load(f)
        
        # Workflow-Name sicherstellen
        workflow["name"] = WORKFLOW_NAME
        return workflow
    
    async def ping_n8n(self) -> bool:
        """Pingt n8n an und prüft Erreichbarkeit"""
        try:
            response = await self.client.get(f"{N8N_HOST}/rest/workflows", headers=self.headers)
            return response.status_code in (200, 401, 403)  # 401/403 = erreichbar, aber auth fehlt
        except Exception as e:
            print(f"❌ n8n not reachable: {e}")
            return False
    
    async def find_workflow_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Sucht Workflow nach Name"""
        try:
            response = await self.client.get(
                f"{N8N_HOST}/rest/workflows",
                headers=self.headers,
                params={"filter[name]": name}
            )
            
            if response.status_code == 200:
                workflows = response.json()
                # n8n gibt Array zurück, suche nach Name
                for workflow in workflows:
                    if workflow.get("name") == name:
                        return workflow
            elif response.status_code in (401, 403):
                print(f"❌ n8n API authentication failed (status {response.status_code})")
                return None
            else:
                print(f"❌ n8n API error (status {response.status_code})")
                return None
                
        except Exception as e:
            print(f"❌ Error searching workflow: {e}")
            return None
        
        return None
    
    async def create_workflow(self, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Erstellt neuen Workflow"""
        try:
            response = await self.client.post(
                f"{N8N_HOST}/rest/workflows",
                headers=self.headers,
                json=workflow_data
            )
            
            if response.status_code in (200, 201):
                print(f"✅ Workflow '{WORKFLOW_NAME}' created")
                return response.json()
            else:
                print(f"❌ Failed to create workflow (status {response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating workflow: {e}")
            return None
    
    async def update_workflow(self, workflow_id: str, workflow_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Aktualisiert bestehenden Workflow"""
        try:
            response = await self.client.patch(
                f"{N8N_HOST}/rest/workflows/{workflow_id}",
                headers=self.headers,
                json=workflow_data
            )
            
            if response.status_code == 200:
                print(f"✅ Workflow '{WORKFLOW_NAME}' updated")
                return response.json()
            else:
                print(f"❌ Failed to update workflow (status {response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error updating workflow: {e}")
            return None
    
    async def activate_workflow(self, workflow_id: str) -> bool:
        """Aktiviert Workflow"""
        try:
            response = await self.client.post(
                f"{N8N_HOST}/rest/workflows/{workflow_id}/activate",
                headers=self.headers
            )
            
            if response.status_code in (200, 204):
                print(f"✅ Workflow '{WORKFLOW_NAME}' activated")
                return True
            else:
                print(f"❌ Failed to activate workflow (status {response.status_code}): {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error activating workflow: {e}")
            return False
    
    def get_webhook_urls(self, workflow_data: Dict[str, Any]) -> list:
        """Extrahiert Webhook-URLs aus Workflow"""
        webhooks = []
        
        for node in workflow_data.get("nodes", []):
            if node.get("type") == "n8n-nodes-base.webhook":
                webhook_path = node.get("parameters", {}).get("path", "")
                if webhook_path:
                    webhooks.append(f"{N8N_HOST}/webhook/{webhook_path}")
        
        return webhooks
    
    async def bootstrap(self) -> bool:
        """Hauptfunktion: Bootstrap des n8n Workflows"""
        print(f"🚀 n8n Bootstrap started")
        print(f"   Host: {N8N_HOST}")
        print(f"   API Key: {'***' + N8N_API_KEY[-4:] if N8N_API_KEY else 'not set'}")
        
        # 1. n8n erreichbar?
        if not await self.ping_n8n():
            print("❌ n8n not reachable, skipping bootstrap")
            return False
        
        # 2. Workflow-JSON laden
        try:
            workflow_data = self.load_workflow_json()
        except Exception as e:
            print(f"❌ Failed to load workflow JSON: {e}")
            return False
        
        # 3. Bestehenden Workflow suchen
        existing_workflow = await self.find_workflow_by_name(WORKFLOW_NAME)
        
        if existing_workflow:
            # Update bestehender Workflow
            workflow_id = existing_workflow["id"]
            updated_workflow = await self.update_workflow(workflow_id, workflow_data)
            
            if not updated_workflow:
                return False
            
            # Prüfen ob bereits aktiv
            if existing_workflow.get("active"):
                print(f"✅ Workflow '{WORKFLOW_NAME}' already active")
            else:
                # Aktivieren
                if not await self.activate_workflow(workflow_id):
                    return False
            
            workflow_result = updated_workflow
            
        else:
            # Neuen Workflow erstellen
            new_workflow = await self.create_workflow(workflow_data)
            
            if not new_workflow:
                return False
            
            # Aktivieren
            workflow_id = new_workflow["id"]
            if not await self.activate_workflow(workflow_id):
                return False
            
            workflow_result = new_workflow
        
        # 4. Summary ausgeben
        webhooks = self.get_webhook_urls(workflow_data)
        
        print(f"\n📊 Bootstrap Summary:")
        print(f"   Name: {workflow_result.get('name', 'Unknown')}")
        print(f"   ID: {workflow_result.get('id', 'Unknown')}")
        print(f"   Active: {workflow_result.get('active', False)}")
        print(f"   Webhooks: {len(webhooks)}")
        
        for webhook in webhooks:
            print(f"     - {webhook}")
        
        print(f"✅ n8n Bootstrap completed successfully")
        return True

async def main():
    """Hauptfunktion"""
    if not N8N_ENABLED:
        print("ℹ️  n8n disabled (N8N_ENABLED=false), skipping bootstrap")
        return 0
    
    if not N8N_API_KEY:
        print("⚠️  N8N_API_KEY not set, authentication may fail")
    
    try:
        async with N8NBootstrap() as bootstrap:
            success = await bootstrap.bootstrap()
            return 0 if success else 1
            
    except Exception as e:
        print(f"❌ Bootstrap failed with exception: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

import requests
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackendIntegration:
    def __init__(self, backend_url="http://127.0.0.1:8001"):
        self.backend_url = backend_url
        self.session = requests.Session()
    
    def authenticate_employee(self, employee_name):
        """Authenticate employee with backend and get employee data"""
        try:
            # Try to find employee by name
            response = self.session.get(f"{self.backend_url}/api/employees/search/", 
                                      params={"name": employee_name})
            
            if response.status_code == 200:
                employees = response.json()
                if employees:
                    return employees[0]  # Return first match
            
            logger.warning(f"Employee {employee_name} not found in backend")
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating employee: {e}")
            return None
    
    def clock_action(self, employee_data, action_type):
        """Perform clock action (in/out/break) via backend API"""
        try:
            # Use the simple clock endpoint that handles all actions
            auth_data = {
                "employee_id": employee_data.get("employee_id"),
                "user_id": employee_data.get("user", {}).get("id"),
                "username": employee_data.get("user", {}).get("username"),
                "action": action_type.lower().replace('_', '_')
            }
            
            response = self.session.post(f"{self.backend_url}/api/simple/clock/", 
                                       json=auth_data,
                                       headers={"Content-Type": "application/json"})
            
            if response.status_code in [200, 201]:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            logger.error(f"Error performing clock action: {e}")
            return {"success": False, "error": str(e)}
    
    def get_employee_status(self, employee_data):
        """Get current clock status for employee"""
        try:
            response = self.session.get(f"{self.backend_url}/api/simple/status/",
                                      params={"employee_id": employee_data.get("employee_id")})
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            logger.error(f"Error getting employee status: {e}")
            return None

# Global integration instance
backend_integration = BackendIntegration()
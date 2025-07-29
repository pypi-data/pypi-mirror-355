# Example: Premium feature with license checking
import hashlib
import hmac
import time
from datetime import datetime, timedelta

class LicenseManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
    
    def generate_license(self, email: str, plan: str, expires_days: int = 365) -> str:
        """Generate a license key for a customer."""
        expires = datetime.now() + timedelta(days=expires_days)
        
        data = {
            "email": email,
            "plan": plan,
            "expires": expires.isoformat(),
            "timestamp": int(time.time())
        }
        
        payload = f"{email}:{plan}:{expires.isoformat()}"
        signature = hmac.new(self.secret_key, payload.encode(), hashlib.sha256).hexdigest()
        
        return f"{payload}:{signature}"
    
    def validate_license(self, license_key: str) -> dict:
        """Validate a license key."""
        try:
            parts = license_key.split(":")
            if len(parts) != 4:
                return {"valid": False, "error": "Invalid format"}
            
            email, plan, expires_iso, signature = parts
            payload = f"{email}:{plan}:{expires_iso}"
            
            # Verify signature
            expected_sig = hmac.new(self.secret_key, payload.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected_sig):
                return {"valid": False, "error": "Invalid signature"}
            
            # Check expiration
            expires = datetime.fromisoformat(expires_iso)
            if datetime.now() > expires:
                return {"valid": False, "error": "License expired"}
            
            return {
                "valid": True,
                "email": email,
                "plan": plan,
                "expires": expires
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e)}

# Example premium feature
def advanced_analytics(data, license_key: str):
    """Premium feature: Advanced Redis analytics."""
    license_mgr = LicenseManager("your-secret-key-here")
    license_info = license_mgr.validate_license(license_key)
    
    if not license_info["valid"]:
        raise Exception(f"Invalid license: {license_info['error']}")
    
    if license_info["plan"] not in ["pro", "enterprise"]:
        raise Exception("Feature requires Pro or Enterprise license")
    
    # Premium analytics logic here
    return {"heatmap": "...", "predictions": "...", "recommendations": "..."}
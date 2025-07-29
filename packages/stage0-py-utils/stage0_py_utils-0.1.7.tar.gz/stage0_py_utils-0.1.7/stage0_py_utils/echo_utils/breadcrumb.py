from datetime import datetime, timezone
import uuid

def create_echo_breadcrumb(token):
    """Create a breadcrumb dictionary from HTTP headers."""
    return {
        "atTime": datetime.now(timezone.utc),
        "byUser": token["user_id"],
        "fromIp": "discord",  
        "correlationId": str(uuid.uuid4())
    }

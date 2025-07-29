from datetime import datetime, timezone
import uuid
from flask import request

def create_flask_breadcrumb(token):
    """Create a breadcrumb dictionary from HTTP headers."""
    return {
        "atTime": datetime.now(timezone.utc),
        "byUser": token["user_id"],
        "fromIp": request.remote_addr,  
        "correlationId": request.headers.get('X-Correlation-Id', str(uuid.uuid4()))  
    }

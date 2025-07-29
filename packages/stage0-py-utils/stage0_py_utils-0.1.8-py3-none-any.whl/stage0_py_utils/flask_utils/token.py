from flask import request

def create_flask_token():
    """Create a access token from the JWT."""
    return {
        # TODO: Get Values from JWT
        "user_id": "aaaa00000000000000000001",
        "roles": ["Staff"]
    }
# Import FastAPI framework to create REST-based control APIs
from fastapi import FastAPI

# Create FastAPI application instance for the Central Controller
app = FastAPI()

# REST API endpoint to provide routing information to KMS nodes
@app.get("/api/v1/route")
def get_route(src: str, dst: str):
    """
    Central Controller:
    This endpoint represents the control plane of the QKD network.
    It returns the relay path between the source and destination KMS.
    """

    # Return a simple direct relay path
    # In the current two-node setup, the path is static
    return {
        "status": "OK",                 # Indicates successful route lookup
        "relay_path": [src, dst]        # Ordered list of nodes forming the path
    }

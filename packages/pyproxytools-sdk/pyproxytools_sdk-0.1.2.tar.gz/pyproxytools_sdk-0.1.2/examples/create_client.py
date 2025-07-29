from pyproxy_sdk.client import PyProxyClient

# Create client
client = PyProxyClient(
    base_url="http://localhost:5000",
    username="admin",
    password="password",
)

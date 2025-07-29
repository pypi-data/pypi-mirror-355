from pyproxy_sdk.client import PyProxyClient
from pyproxy_sdk.exceptions import PyProxyAlreadyExists

# Create client
client = PyProxyClient(
    base_url="http://localhost:5000",
    username="admin",
    password="password",
)

# Add URLs to blocklist
try:
    client.add_filtering("url", "example.com/test")
except PyProxyAlreadyExists:
    print("This URLs is already blocked.")

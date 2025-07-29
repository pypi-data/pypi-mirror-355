from pyproxy_sdk.client import PyProxyClient
from pyproxy_sdk.exceptions import PyProxyNotFound

# Create client
client = PyProxyClient(
    base_url="http://localhost:5000",
    username="admin",
    password="password",
)

# Delete domain from blocklist
try:
    client.delete_filtering("domain", "example.com")
except PyProxyNotFound:
    print("This domain is not blocked.")

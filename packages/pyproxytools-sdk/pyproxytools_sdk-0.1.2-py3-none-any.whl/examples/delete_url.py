from pyproxy_sdk.client import PyProxyClient
from pyproxy_sdk.exceptions import PyProxyNotFound

# Create client
client = PyProxyClient(
    base_url="http://localhost:5000",
    username="admin",
    password="password",
)

# Delete URL from blocklist
try:
    client.delete_filtering("url", "example.com/test")
except PyProxyNotFound:
    print("This URL is not blocked.")

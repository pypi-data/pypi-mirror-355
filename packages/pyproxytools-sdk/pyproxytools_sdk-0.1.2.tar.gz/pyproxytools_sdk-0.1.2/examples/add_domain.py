from pyproxy_sdk.client import PyProxyClient
from pyproxy_sdk.exceptions import PyProxyAlreadyExists

# Create client
client = PyProxyClient(
    base_url="http://localhost:5000",
    username="admin",
    password="password",
)

# Add domain to blocklist
try:
    client.add_filtering("domain", "example.com")
except PyProxyAlreadyExists:
    print("This domain is already blocked.")

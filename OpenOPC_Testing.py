from opcua import Client, ua
from opcua.ua import ExtensionObject
import services.opcua_structures as opcua_structures

server_url = "opc.tcp://172.16.1.192:56000"
client = Client(server_url)
client.connect()

# Get the node
node = client.get_node("ns=2;s=Work.CurrentJob")

# Get the node's data type definition (NodeId)
datatype_def = node.get_data_type()
# Get the BrowseName of the data type (e.g., JobInfo)
datatype_node = client.get_node(datatype_def)
browse_name = datatype_node.get_browse_name()
datatype_name = browse_name.Name  # e.g., "JobInfo"

# Map to the correct Python class
StructClass = opcua_structures.map_structures(datatype_name)

# Get the value from the node (should be an ExtensionObject)
node_value = node.get_value()

# If it's an ExtensionObject, decode it using the mapped class
if isinstance(node_value, ExtensionObject) and StructClass:
    struct_instance = StructClass(node_value.Body)
    print(struct_instance.as_dict())
else:
    print("Node value is not an ExtensionObject or no mapping found.")

client.disconnect()
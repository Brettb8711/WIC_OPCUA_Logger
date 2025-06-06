from opcua import Client

# This file was moved to services/opcua_service.py for better project structure.

class OPCUAService:
    def __init__(self, url):
        self.url = url
        self.client = None

    def connect(self):
        self.client = Client(self.url)
        self.client.connect()
        return self.client

    def disconnect(self):
        if self.client:
            self.client.disconnect()
            self.client = None
    
    def get_nodes(self):
        ''' 
        This function retrieves all children nodes from a OPCUA server.
        
        Parameters
        ----------
        self: Instance of the OPCUAService class.
            
        Returns
        -------
        nodes_list: A list of dictionaries containing node names and their IDs.
        '''
        def get_children(nodes_list, node, indent=0):
            ''' Recursively retrieves children nodes and appends them to the nodes_list with indentation '''
            try:
                children = node.get_children()
                for child in children:
                    try:
                        name = child.get_display_name().Text
                        nodes_list.append({'name': "    " * indent + name, 'nodeid': str(child.nodeid)})
                        get_children(nodes_list, child, indent + 1)
                    except Exception:
                        continue
            except Exception as e:
                pass
            return nodes_list
        
        if not self.client:
            raise Exception('Not connected')
        
        objects = self.client.get_objects_node()
        nodes = []
        get_children(nodes, objects, 0)
        return nodes
    
    def get_value(self, node_id):
        '''
        This function retrieves the value of a node from the OPCUA server.
        Parameters
        ----------
        node_id: The NodeId of the node whose value is to be retrieved.

        Returns
        -------
        value: The value of the node, which can be of various types (int, float, bool, etc.).'''
        if not self.client:
            raise Exception('Not connected')
        node = self.client.get_node(node_id)
        return node.get_value()
    
    def get_datatype(self, node_id):
        '''
        This function retrieves the data type of a node from the OPCUA server.
        Parameters
        ----------
        node_id: The NodeId of the node whose data type is to be retrieved.
        
        Returns
        -------
        browse_name: The BrowseName of the node's data type, which is a string representation of the data type.
        Raises
        '''
        if not self.client:
            raise Exception('Not connected')
        node = self.client.get_node(node_id)
        dtype = node.get_data_type()
        return self.client.get_node(dtype).get_browse_name()

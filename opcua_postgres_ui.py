import sys
from PyQt5.QtWidgets import (
    QApplication, QHeaderView, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QMessageBox, QDialog, QComboBox, QTableWidget, QTableWidgetItem, QSpinBox
)
from PyQt5.QtCore import QTimer, Qt
from services.opcua_service import OPCUAService
from services.postgres_service import PostgresService
from opcua.ua import ExtensionObject
import services.opcua_structures as opcua_structures
import services.config_service as config_service

class AddConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add/Edit OPC UA Connection')
        self.resize(500, 400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.edit_btn = QPushButton('Edit Existing Server Nodes', self)
        self.edit_btn.setEnabled(True)
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        self.layout.addWidget(self.edit_btn)
        self.info_label = QLabel('Enter OPC UA Server Info:', self)
        self.layout.addWidget(self.info_label)
        self.display_name_input = QLineEdit(self)
        self.display_name_input.setPlaceholderText('Server Display Name')
        self.layout.addWidget(self.display_name_input)
        self.server_url_input = QLineEdit(self)
        self.server_url_input.setPlaceholderText('OPC UA Server URL (e.g., opc.tcp://localhost:4840)')
        self.layout.addWidget(self.server_url_input)
        self.refresh_rate_input = QSpinBox(self)
        self.refresh_rate_input.setMinimum(1)
        self.refresh_rate_input.setMaximum(3600)
        self.refresh_rate_input.setValue(10)
        self.layout.addWidget(QLabel('Refresh Rate (seconds):'))
        self.layout.addWidget(self.refresh_rate_input)
        self.test_btn = QPushButton('Test Connection', self)
        self.test_btn.clicked.connect(self.test_connection)
        self.layout.addWidget(self.test_btn)
        self.load_btn = QPushButton('Load Nodes', self)
        self.load_btn.clicked.connect(self.load_nodes)
        self.layout.addWidget(self.load_btn)
        self.progress = QLabel('', self)
        self.layout.addWidget(self.progress)
        self.node_list = QListWidget(self)
        self.node_list.setSelectionMode(self.node_list.MultiSelection)
        self.layout.addWidget(self.node_list)
        self.log_btn = QPushButton('Log Selected Nodes', self)
        self.log_btn.setEnabled(False)
        self.log_btn.clicked.connect(self.accept)
        self.layout.addWidget(self.log_btn)
        self.opc_service = None
        self.selected_nodes = []
        self.tested = False

    def open_edit_dialog(self):
        dlg = EditConnectionDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.display_name_input.setText(dlg.display_name_input.text().strip())
            self.server_url_input.setText(dlg.server_url_input.text().strip())
            self.refresh_rate_input.setValue(dlg.refresh_rate_input.value())
            self.opc_service = dlg.opc_service
            self.selected_nodes = dlg.selected_nodes
            self.tested = True
            self.load_nodes()

    def test_connection(self):
        url = self.server_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, 'Input Error', 'Please enter the OPC UA server URL.')
            return
        try:
            opc_service = OPCUAService(url)
            opc_service.connect()
            opc_service.disconnect()
            QMessageBox.information(self, 'Success', 'Successfully connected to OPC UA server.')
            self.tested = True
        except Exception as e:
            QMessageBox.critical(self, 'Connection Error', str(e))
            self.tested = False

    def load_nodes(self):
        # Check if the connection has been tested
        if not self.tested:
            QMessageBox.warning(self, 'Test Required', 'Please test the connection first.')
            return
        url = self.server_url_input.text().strip()
        self.progress.setText('Loading Nodes from the server...')
        QApplication.processEvents()
        try:
            self.opc_service = OPCUAService(url)
            self.opc_service.connect()
            nodes = self.opc_service.get_nodes()
            self.node_list.clear()
            for node in nodes:
                self.node_list.addItem(f'{node["name"]} ({node["nodeid"]})')
            self.progress.setText('Select nodes to log:')
            self.log_btn.setEnabled(True)
        except Exception as e:
            self.progress.setText('Failed to load nodes.')
            QMessageBox.critical(self, 'Connection Error', str(e))

    def accept(self):
        self.selected_nodes = [item.text().split('(')[-1][:-2] for item in self.node_list.selectedItems()]
        # Save the connection details to the config file
        self.save_connection()
        if not self.selected_nodes:
            QMessageBox.warning(self, 'Selection Error', 'Please select at least one node.')
            return
        super().accept()

    def save_connection(self):
        # Save the connection details to the config file
        display_name = self.display_name_input.text().strip()
        url = self.server_url_input.text().strip()
        refresh_rate = self.refresh_rate_input.value()
        config = config_service.load_config()
        opcua_servers = config.get('opcua_servers', [])
        for server in opcua_servers:
            if server.get('display_name') == display_name:
                server['url'] = url
                server['refresh_rate'] = refresh_rate
                server['nodes'] = self.selected_nodes
                break
        else:
            opcua_servers.append({
                'display_name': display_name,
                'url': url,
                'refresh_rate': refresh_rate,
                'nodes': self.selected_nodes
            })
        config['opcua_servers'] = opcua_servers
        config_service.save_config(config)

class AddDatabaseDialog(QDialog):
    def __init__(self, parent=None):
        config = config_service.load_config()
        db_info = config.get('database', {})
        super().__init__(parent)
        self.setWindowTitle('Add Postgres Database Connection')
        self.resize(400, 300)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        # Database Name
        self.db_label = QLabel('Database Name:')
        self.layout.addWidget(self.db_label)
        self.db_input = QLineEdit(self)
        if db_info and 'dbname' in db_info:
            self.db_input.setText(db_info['dbname'])
        self.layout.addWidget(self.db_input)
        # User
        self.user_label = QLabel('User:')
        self.layout.addWidget(self.user_label)
        self.user_input = QLineEdit(self)
        if db_info and 'user' in db_info:
            self.user_input.setText(db_info['user'])
        self.layout.addWidget(self.user_input)
        # Password
        self.pw_label = QLabel('Password:')
        self.layout.addWidget(self.pw_label)
        self.pw_input = QLineEdit(self)
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.pw_input)
        # Host
        self.host_label = QLabel('Host:')
        self.layout.addWidget(self.host_label)
        self.host_input = QLineEdit(self)
        self.host_input.setText('localhost')
        self.layout.addWidget(self.host_input)
        # Test and Save
        self.test_btn = QPushButton('Test Connection', self)
        self.test_btn.clicked.connect(self.test_connection)
        self.layout.addWidget(self.test_btn)
        self.save_btn = QPushButton('Save Connection', self)
        self.save_btn.clicked.connect(self.accept)
        self.save_btn.setEnabled(False)
        self.layout.addWidget(self.save_btn)
        self.conn_str = ''
        self.tested = False

    def test_connection(self):
        db = self.db_input.text().strip()
        user = self.user_input.text().strip()
        pw = self.pw_input.text().strip()
        host = self.host_input.text().strip()
        conn_str = f'dbname={db} user={user} password={pw} host={host}'
        try:
            pg_service = PostgresService(conn_str)
            pg_service.test_connection()
            QMessageBox.information(self, 'Success', 'Successfully connected to Postgres database.')
            self.conn_str = conn_str
            self.tested = True
            self.save_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, 'Database Error', str(e))
            self.tested = False
            self.save_btn.setEnabled(False)

    def accept(self):
        if not self.tested:
            QMessageBox.warning(self, 'Test Required', 'Please test the connection before saving.')
            return
        super().accept()

class OPCUAClientUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('OPC UA to Postgres Collector')
        self.resize(1200, 750)
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        # Top: Filter selector
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel('Show nodes for server:'))
        self.server_filter = QComboBox()
        self.server_filter.addItem('All')
        self.server_filter.currentIndexChanged.connect(self.update_node_table)
        filter_layout.addWidget(self.server_filter)
        main_layout.addLayout(filter_layout)
        # Node table
        node_layout = QHBoxLayout()
        self.node_table = QTableWidget(0, 6)
        self.node_table.setHorizontalHeaderLabels(['Node ID', 'Node Name','Server Display Name', 'Last Value', 'DataType','Timestamp'])
        self.node_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        node_layout.addWidget(self.node_table)
        main_layout.addLayout(node_layout)
        # Right: OPC server info and DB info
        controls_layout = QHBoxLayout()
        # OPC server info
        self.opc_group = QWidget()
        opc_layout = QVBoxLayout()
        self.opc_group.setLayout(opc_layout)
        opc_layout.addWidget(QLabel('Add OPC UA Connection'))
        self.add_connection_btn = QPushButton('Edit Existing or Add New Connection', self)
        self.add_connection_btn.clicked.connect(self.open_add_connection_dialog)
        opc_layout.addWidget(self.add_connection_btn)
        self.edit_connection_button = QPushButton('Load Saved Server Connections', self)
        self.edit_connection_button.clicked.connect(self.load_opcua_config)
        opc_layout.addWidget(self.edit_connection_button)
        controls_layout.addWidget(self.opc_group)
        # DB info
        self.db_group = QWidget()
        db_layout = QVBoxLayout()
        self.db_group.setLayout(db_layout)
        db_layout.addWidget(QLabel('Database Info'))
        self.add_db_btn = QPushButton('Add Database Connection', self)
        self.add_db_btn.clicked.connect(self.open_add_db_dialog)
        db_layout.addWidget(self.add_db_btn)
        self.edit_db_button = QPushButton('Edit/Select Databases', self)
        self.edit_db_button.clicked.connect(self.open_add_db_dialog)
        db_layout.addWidget(self.edit_db_button)
        self.pg_conn_input = QLineEdit(self)
        self.pg_conn_input.setReadOnly(True)
        self.pg_conn_input.hide()
        db_layout.addWidget(self.pg_conn_input)
        controls_layout.addWidget(self.db_group)
        main_layout.addLayout(controls_layout)
        # Data
        self.servers = []  # List of dicts: {opc_service, pg_service, display_name, refresh_rate, nodes, timers, url}
        self.pg_service = None
        self.node_data = []  # List of dicts: {node_id, node_name, server_display_name, last_value, timestamp}

    # Load existing config
    def load_opcua_config(self):
        config = config_service.load_config()
        opcua_servers = config.get('opcua_servers', [])
        for server in opcua_servers:
            url = server.get('url', '')
            display_name = server.get('display_name', url)
            refresh_rate = server.get('refresh_rate', 10)
            nodes = server.get('nodes', [])
            # Get Postgres connection string
            pg_conn_str = self.pg_conn_input.text().strip()
            if not pg_conn_str:
                QMessageBox.warning(self, 'Input Error', 'Please add a database connection first.')
                return
            
            # Add the server to the filter if not already present
            if display_name not in [self.server_filter.itemText(i) for i in range(self.server_filter.count())]:
                self.server_filter.addItem(display_name)

            # Skip if no URL or Postgres connection string
            
            try:
                opc_service = OPCUAService(url)
                opc_service.connect()
                timer = QTimer()
                pg_service = PostgresService(pg_conn_str)
                pg_service.connect() 
                server_info = {
                    'opc_service': opc_service,
                    'pg_service': pg_service,
                    'display_name': display_name,
                    'refresh_rate': refresh_rate,
                    'nodes': nodes,
                    'timer': timer,
                    'url': url,
                    'disconnected': False,
                    'retry_timer': None  
                }
                timer.timeout.connect(lambda s=server_info: self.update_node_values_multi(s))
                timer.start(refresh_rate * 1000)
                self.servers.append(server_info)
                # Add nodes to node_data
                for node_id in nodes:
                    node_name = node_id.split(';')[1]
                    node_name = node_name[2:]  # Optionally parse for better name
                    node_name = node_name.split('.')[1]
                    self.node_data.append({
                        'node_id': node_id,
                        'node_name': node_name,
                        'server_display_name': display_name,
                        'last_value': '',
                        'datatype': '',  # Placeholder for datatype
                        'timestamp': ''
                    })
                self.update_node_table()
            except Exception as e:
                QMessageBox.critical(self, 'Connection Error', f'Failed to connect to server {display_name}: {str(e)}')
                pass  # Optionally log error

    def open_add_connection_dialog(self):
        dlg = AddConnectionDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            url = dlg.server_url_input.text().strip()
            display_name = dlg.display_name_input.text().strip() or url
            refresh_rate = dlg.refresh_rate_input.value()
            selected_nodes = dlg.selected_nodes
            opc_service = dlg.opc_service
            # Add server to filter if new
            if display_name not in [self.server_filter.itemText(i) for i in range(self.server_filter.count())]:
                self.server_filter.addItem(display_name)
            # Start logging (if DB info is set)
            pg_conn_str = self.pg_conn_input.text().strip()
            if pg_conn_str:
                try:
                    if not self.pg_service:
                        self.pg_service = PostgresService(pg_conn_str)
                        self.pg_service.connect()
                    timer = QTimer()
                    server_info = {
                        'opc_service': opc_service,
                        'pg_service': self.pg_service,
                        'display_name': display_name,
                        'refresh_rate': refresh_rate,
                        'nodes': selected_nodes,
                        'timer': timer,
                        'url': url
                    }
                    timer.timeout.connect(lambda s=server_info: self.update_node_values_multi(s))
                    timer.start(refresh_rate * 1000)
                    self.servers.append(server_info)
                    # Add nodes to node_data
                    for node_id in selected_nodes:
                        node_name = node_id.split(';')[1]
                        node_name = node_name[2:]  # Optionally parse for better name
                        node_name = node_name.split('.')[1]
                        self.node_data.append({
                            'node_id': node_id,
                            'node_name': node_name,
                            'server_display_name': display_name,
                            'last_value': '',
                            'datatype': '',  # Placeholder for datatype
                            'timestamp': ''
                        })
                    self.update_node_table()
                except Exception as e:
                    QMessageBox.critical(self, 'DB Error', str(e))

    def open_add_db_dialog(self):
        dlg = AddDatabaseDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            self.pg_conn_input.setText(dlg.conn_str)
            try:
                self.pg_service = PostgresService(dlg.conn_str)
                self.pg_service.connect()
                QMessageBox.information(self, 'Success', 'Database connection saved and ready!')
            except Exception as e:
                QMessageBox.critical(self, 'Database Error', str(e))

    def test_db_connection(self):
        conn_str = self.pg_conn_input.text().strip()
        if not conn_str:
            QMessageBox.warning(self, 'Input Error', 'Please add and test a database connection first.')
            return
        try:
            pg_service = PostgresService(conn_str)
            pg_service.test_connection()
            QMessageBox.information(self, 'Success', 'Successfully connected to Postgres database.')
        except Exception as e:
            QMessageBox.critical(self, 'Database Error', str(e))
    
    def update_node_values_multi(self, server_info):
        for node_id in server_info['nodes']:
            try:
                value = server_info['opc_service'].get_value(node_id)
                datatype_node = server_info['opc_service'].get_datatype(node_id)
                datatype_name = datatype_node.Name
                datatype_id = datatype_node.NamespaceIndex
                

                if datatype_id == 2:  # Assuming namespace index 2 is for custom structures
                    StructClass = opcua_structures.map_structures(datatype_name)
                    if StructClass:
                        value = server_info['opc_service'].get_value(node_id)
                        if isinstance(value, ExtensionObject):
                            struct_instance = StructClass(value.Body)
                            value = struct_instance.as_dict()
                        else:
                            # It is an array of ExtensionObjects
                            value = [StructClass(item.Body).as_dict() for item in value if isinstance(item, ExtensionObject)]
                            value = str(value)
                
                
                server_info['pg_service'].insert_data(node_id, value, server_info['display_name'])
                # Update node_data
                for node in self.node_data:
                    if node['node_id'] == node_id and node['server_display_name'] == server_info['display_name']:
                        node['last_value'] = str(value)
                        from datetime import datetime
                        node['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        node['datatype'] = datatype_name  # Store datatype name
                        #node['node_display_name'] = self.client.get_node(node_id).get_browse_name().Name  # Store display name

                self.update_node_table()
                server_info['disconnected'] = False
            except Exception as e:
                print(f"Error reading from server {server_info['display_name']}: {e}")
                if not server_info.get('disconnected', False):
                    server_info['disconnected'] = True
                    self.handle_server_disconnect(server_info)
                # Optionally show error in UI
                pass
    def handle_server_disconnect(self, server_info):
        # Stop the regular polling timer
        server_info['timer'].stop()
        print(f"Server {server_info['display_name']} disconnected. Will retry in 5 minutes.")

        # Start a retry timer if not already started
        if not server_info.get('retry_timer'):
            retry_timer = QTimer()
            retry_timer.setSingleShot(False)
            retry_timer.timeout.connect(lambda: self.try_reconnect_server(server_info))
            retry_timer.start(5 * 60 * 1000)  # 5 minutes
            server_info['retry_timer'] = retry_timer

    def try_reconnect_server(self, server_info):
        try:
            print(f"Attempting to reconnect to {server_info['display_name']}...")
            server_info['opc_service'].connect()
            # Optionally reload nodes if needed
            nodes = server_info['opc_service'].get_nodes()
            server_info['nodes'] = [n["nodeid"] for n in nodes]
            # Restart the regular polling timer
            server_info['timer'].start(server_info['refresh_rate'] * 1000)
            # Stop the retry timer
            if server_info.get('retry_timer'):
                server_info['retry_timer'].stop()
                server_info['retry_timer'] = None
            server_info['disconnected'] = False
            print(f"Reconnected to {server_info['display_name']}.")
        except Exception as e:
            print(f"Reconnect failed for {server_info['display_name']}: {e}")
            # Will retry again in 5 minutes automatically

    def update_node_table(self):
        filter_name = self.server_filter.currentText()
        filtered = [n for n in self.node_data if filter_name == 'All' or n['server_display_name'] == filter_name]
        self.node_table.setRowCount(len(filtered))
        for row, node in enumerate(filtered):
            self.node_table.setItem(row, 0, QTableWidgetItem(node['node_id']))
            self.node_table.setItem(row, 1, QTableWidgetItem(node['node_name']))
            self.node_table.setItem(row, 2, QTableWidgetItem(node['server_display_name']))
            self.node_table.setItem(row, 3, QTableWidgetItem(node['last_value']))
            self.node_table.setItem(row, 4, QTableWidgetItem(node['datatype']))
            self.node_table.setItem(row, 5, QTableWidgetItem(node['timestamp']))

class EditConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Edit OPC UA Connection')
        self.resize(500, 400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.list_label = QLabel('Select an OPC UA Server to Edit:', self)
        self.layout.addWidget(self.list_label)
        self.server_list = QListWidget(self)
        self.server_list.setSelectionMode(self.server_list.SingleSelection)
        self.server_list.currentItemChanged.connect(self.update_server_info)
        self.layout.addWidget(self.server_list)

        self.info_label = QLabel('Edit OPC UA Server Info:', self)
        self.layout.addWidget(self.info_label)
        self.display_name_input = QLineEdit(self)
        self.display_name_input.setPlaceholderText('Server Display Name')
        self.layout.addWidget(self.display_name_input)
        self.server_url_input = QLineEdit(self)
        self.server_url_input.setPlaceholderText('OPC UA Server URL (e.g., opc.tcp://localhost:4840)')
        self.layout.addWidget(self.server_url_input)
        self.refresh_rate_input = QSpinBox(self)
        self.refresh_rate_input.setMinimum(1)
        self.refresh_rate_input.setMaximum(3600)
        self.layout.addWidget(QLabel('Refresh Rate (seconds):'))
        self.layout.addWidget(self.refresh_rate_input)
        self.update_server_list()  # Load existing servers into the list
        # Add buttons for testing connection and loading nodes
        self.test_btn = QPushButton('Test Connection', self)
        self.test_btn.clicked.connect(self.test_connection)
        self.layout.addWidget(self.test_btn)
        self.load_btn = QPushButton('Load Nodes', self)
        self.load_btn.clicked.connect(self.load_nodes)
        self.layout.addWidget(self.load_btn)
        # Add a button to save changes
        self.save_btn = QPushButton('Save Changes', self)
        self.save_btn.clicked.connect(self.save_changes)
        self.layout.addWidget(self.save_btn)
        # Create a widget for the node list
        self.node_list = QListWidget(self) 
        self.node_list.setSelectionMode(self.node_list.MultiSelection)
        self.layout.addWidget(self.node_list)

    def save_changes(self):
        # Save the changes made to the selected OPC UA server to the config file
        selected_item = self.server_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, 'Selection Error', 'Please select a server to save changes.')
            return
        display_name = self.display_name_input.text().strip()
        url = self.server_url_input.text().strip()  
        refresh_rate = self.refresh_rate_input.value()
        if not display_name or not url:
            QMessageBox.warning(self, 'Input Error', 'Please fill in all fields.')
            return
        config = config_service.load_config()
        opcua_servers = config.get('opcua_servers', [])
        for server in opcua_servers:
            if server.get('display_name') == selected_item.text():
                server['display_name'] = display_name
                server['url'] = url
                server['refresh_rate'] = refresh_rate
                server['nodes'] = [item.text().split('(')[-1][:-2] for item in self.node_list.selectedItems()]
                break
            else:
                # If the server is not found, add a new entry
                opcua_servers.append({
                    'display_name': display_name,
                    'url': url,
                    'refresh_rate': refresh_rate,
                    'nodes': [item.text().split('(')[-1][:-2] for item in self.node_list.selectedItems()]
                })
        config['opcua_servers'] = opcua_servers
        config_service.save_config(config)

    def test_connection(self):
        url = self.server_url_input.text().strip()
        if not url:
            QMessageBox.warning(self, 'Input Error', 'Please enter the OPC UA server URL.')
            return
        try:
            opc_service = OPCUAService(url)
            opc_service.connect()
            opc_service.disconnect()
            QMessageBox.information(self, 'Success', 'Successfully connected to OPC UA server.')
        except Exception as e:
            QMessageBox.critical(self, 'Connection Error', str(e))
    
    def load_nodes(self):
        # Load the nodes from the selected server from the config file to the node list
        selected_item = self.server_list.currentItem()
        if not selected_item:
            QMessageBox.warning(self, 'Selection Error', 'Please select a server to load nodes.')
            return
        display_name = selected_item.text()
        config = config_service.load_config()
        opcua_servers = config.get('opcua_servers', [])
        for server in opcua_servers:
            if server.get('display_name') == display_name:
                url = server.get('url', '')
                opc_service = OPCUAService(url)
                opc_service.connect()
                nodes = opc_service.get_nodes()
                self.node_list.clear()
                for node in nodes:
                    self.node_list.addItem(f'{node["name"]} ({node["nodeid"]})')
                opc_service.disconnect()
                break
    
    def update_server_info(self):
        # Get the selected server from the list
        selected_item = self.server_list.currentItem()
        # Fill the input fields with the selected server's info
        if selected_item:
            display_name = selected_item.text()
            config = config_service.load_config()
            opcua_servers = config.get('opcua_servers', [])
            for server in opcua_servers:
                if server.get('display_name') == display_name:
                    self.display_name_input.setText(server.get('display_name', ''))
                    self.server_url_input.setText(server.get('url', ''))
                    self.refresh_rate_input.setValue(server.get('refresh_rate', 10))
                    self.selected_nodes = server.get('nodes', [])
                    break

    def update_server_list(self):
        self.server_list.clear()
        config = config_service.load_config()
        opcua_servers = config.get('opcua_servers', [])
        for server in opcua_servers:
            display_name = server.get('display_name', server.get('url', ''))
            self.server_list.addItem(display_name)
    
    def load_server_config(self):
        config = config_service.load_config()
        opcua_servers = config.get('opcua_servers', [])
        for server in opcua_servers:
            url = server.get('url', '')
            display_name = server.get('display_name', url)
            refresh_rate = server.get('refresh_rate', 10)
            nodes = server.get('nodes', [])

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OPCUAClientUI()
    window.show()
    sys.exit(app.exec_())

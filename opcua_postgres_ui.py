import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QListWidget, QMessageBox, QDialog, QComboBox, QTableWidget, QTableWidgetItem, QSpinBox
)
from PyQt5.QtCore import QTimer, Qt
from opcua_service import OPCUAService
from postgres_service import PostgresService

class AddConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Add OPC UA Connection')
        self.resize(500, 400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
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
        if not self.selected_nodes:
            QMessageBox.warning(self, 'Selection Error', 'Please select at least one node.')
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
        self.node_table = QTableWidget(0, 4)
        self.node_table.setHorizontalHeaderLabels(['Node Name', 'Server Display Name', 'Last Value', 'Timestamp'])
        main_layout.addWidget(self.node_table)
        # Right: OPC server info and DB info
        controls_layout = QHBoxLayout()
        # OPC server info
        self.opc_group = QWidget()
        opc_layout = QVBoxLayout()
        self.opc_group.setLayout(opc_layout)
        opc_layout.addWidget(QLabel('Add OPC UA Connection'))
        self.add_connection_btn = QPushButton('Add New Connection', self)
        self.add_connection_btn.clicked.connect(self.open_add_connection_dialog)
        opc_layout.addWidget(self.add_connection_btn)
        controls_layout.addWidget(self.opc_group)
        # DB info
        self.db_group = QWidget()
        db_layout = QVBoxLayout()
        self.db_group.setLayout(db_layout)
        db_layout.addWidget(QLabel('Database Info'))
        self.pg_conn_input = QLineEdit(self)
        self.pg_conn_input.setPlaceholderText('Postgres connection string (e.g., dbname=opcua user=postgres password=secret host=localhost)')
        self.pg_conn_input.setText('dbname= user=postgres password= host=localhost')
        db_layout.addWidget(self.pg_conn_input)
        self.test_db_btn = QPushButton('Test Database Connection', self)
        self.test_db_btn.clicked.connect(self.test_db_connection)
        db_layout.addWidget(self.test_db_btn)
        controls_layout.addWidget(self.db_group)
        main_layout.addLayout(controls_layout)
        # Data
        self.servers = []  # List of dicts: {opc_service, pg_service, display_name, refresh_rate, nodes, timers, url}
        self.pg_service = None
        self.node_data = []  # List of dicts: {node_id, node_name, server_display_name, last_value, timestamp}

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
                        node_name = node_id  # Optionally parse for better name
                        self.node_data.append({
                            'node_id': node_id,
                            'node_name': node_name,
                            'server_display_name': display_name,
                            'last_value': '',
                            'timestamp': ''
                        })
                    self.update_node_table()
                except Exception as e:
                    QMessageBox.critical(self, 'DB Error', str(e))

    def test_db_connection(self):
        conn_str = self.pg_conn_input.text().strip()
        if not conn_str:
            QMessageBox.warning(self, 'Input Error', 'Please enter the Postgres connection string.')
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
                server_info['pg_service'].insert_data(node_id, value, server_info['url'])
                # Update node_data
                for node in self.node_data:
                    if node['node_id'] == node_id and node['server_display_name'] == server_info['display_name']:
                        node['last_value'] = str(value)
                        from datetime import datetime
                        node['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self.update_node_table()
            except Exception as e:
                # Optionally show error in UI
                pass

    def update_node_table(self):
        filter_name = self.server_filter.currentText()
        filtered = [n for n in self.node_data if filter_name == 'All' or n['server_display_name'] == filter_name]
        self.node_table.setRowCount(len(filtered))
        for row, node in enumerate(filtered):
            self.node_table.setItem(row, 0, QTableWidgetItem(node['node_name']))
            self.node_table.setItem(row, 1, QTableWidgetItem(node['server_display_name']))
            self.node_table.setItem(row, 2, QTableWidgetItem(node['last_value']))
            self.node_table.setItem(row, 3, QTableWidgetItem(node['timestamp']))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OPCUAClientUI()
    window.show()
    sys.exit(app.exec_())

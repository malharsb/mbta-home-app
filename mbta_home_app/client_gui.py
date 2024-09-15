import socket
import time
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow


HOST = "127.0.0.1"
PORT = 65432
DEFAULT_STATION = "DEFAULT STATION"
BACKGROUND_IMAGE_PATH = "mbta_home_app/red_line_background.jpg"


class SocketClient:
    def __init__(self):
        self._host = HOST
        self._port = PORT
    
    def get_arrival_predictions(self, station_name):

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            
            s.connect((self._host, self._port))

            message = f"{station_name}"
            s.sendall(message.encode("utf-8"))
            res = s.recv(1024).decode('utf-8')

            pred_times = res.split(",")
            print("result is: ", pred_times)
            return pred_times



# Create a subclass of QMainWindow to set up the main window
class MainWindow(QMainWindow):
    def __init__(self, station_name):
        super().__init__()
        self._mbta_home_app_client = SocketClient()
        self._station_name = station_name

        # Set the window title
        self.setWindowTitle("MBTA Home App")
        self.setGeometry(100, 100, 980, 480)

        # Create a QLabel widget to display the background image
        self.background_label = QLabel(self)
        self.background_label.setGeometry(0, 0, 1980, 980)

        # Load the background image using QPixmap
        pixmap = QPixmap(BACKGROUND_IMAGE_PATH)
        self.background_label.setPixmap(pixmap)
        self.background_label.setScaledContents(True)  # Scale the image to fit the window
        
        # Create the first QLabel widget
        self.label_station_name = QLabel(self._station_name, self)
        self.label_station_name.setGeometry(380, 60, 1200, 150)
        self.label_station_name.setStyleSheet("color: white; font-size: 128px; font-weight: bold;")

        # Create the first QLabel widget
        self.label_northbound_name = QLabel("NORTHBOUND", self)
        self.label_northbound_name.setGeometry(200, 300, 1200, 150)
        self.label_northbound_name.setStyleSheet("color: black; font-size: 64px; font-weight: bold;")

        # Create the first QLabel widget
        self.label_southbound_name = QLabel("SOUTHBOUND", self)
        self.label_southbound_name.setGeometry(1200, 300, 1200, 150)
        self.label_southbound_name.setStyleSheet("color: black; font-size: 64px; font-weight: bold;")

        # Create the first QLabel widget
        self.label_nb = QLabel("N/A\nN/A\nN/A", self)
        self.label_nb.setGeometry(250, 350, 500, 500)
        self.label_nb.setStyleSheet("color: black; font-size: 64px; font-weight: bold;")

        # Create the second QLabel widget
        self.label_sb = QLabel("N/A\nN/A\nN/A", self)
        self.label_sb.setGeometry(1250, 350, 500, 500)
        self.label_sb.setStyleSheet("color: black; font-size: 64px; font-weight: bold;")

        # Create a QTimer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.get_latest_predictions)  # Connect the timeout signal to the update_labels method
        self.timer.start(5000)  # Update every 5000 ms (5 seconds)

    def get_latest_predictions(self):
        """Get raw arrival predictions from the server"""
        
        preds = self._mbta_home_app_client.get_arrival_predictions(self._station_name)
        preds = list(map(lambda x: str(int(float(x))), preds))

        nb_preds = preds[:3]
        sb_preds = preds[3:]

        self.label_nb.setText(" MINS\n".join(nb_preds) + " MINS")
        self.label_sb.setText(" MINS\n".join(sb_preds) + " MINS")


class GUI:
    def __init__(self, station_name):
        # Create an instance of QApplication
        app = QApplication(sys.argv)

        # Create an instance of the main window
        window = MainWindow(station_name)

        # Show the window
        window.show()

        # Execute the application's main loop
        sys.exit(app.exec_())
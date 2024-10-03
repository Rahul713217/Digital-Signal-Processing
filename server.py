import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel,QGroupBox,QPushButton,QLineEdit
from PyQt5.QtCore import Qt
from matplotlib.animation import FuncAnimation

from scipy.signal import find_peaks  

# Imports
import socket
import select
import struct
import time


class recieve_scan_UDP:
    
    def __init__(self, ip_address, port):
        self.sock = self.init_UDP_COMM(ip_address, port)
    
    def init_UDP_COMM(self, ip_address, port):
        # Create a UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind the socket to the port
        server_address = (ip_address, port)
        sock.bind(server_address)

        # Set socket to non-blocking mode
        sock.setblocking(False)

        return sock

    def receive_scan_data(self):
        
        # Use select to check if data is available
        readable, _, _ = select.select([self.sock], [], [], 0)

        if self.sock in readable:
            try:
                # Attempt to receive data
                self.data, self.addr = self.sock.recvfrom(4096)  # Buffer size is 4096 bytes
                self.data_size = len(self.data)
                print(f"Received {self.data_size} bytes from {self.addr}")
                return self.data, self.data_size
            except BlockingIOError:
                # No data available to read
                print("BlockingIOError: No data available on the port")
                return None, 0
        else:
            print("No readable data on the port")
            return None, 0

    def parse_scan_data(self):
        # Unpack the data.... 1 bytes each (unsigned char)
        self.samples = struct.unpack('516b', self.data)
        return self.samples


class MainWindow(QMainWindow):
    def __init__(self, rcv_udp_object, frames=60, fps=50, threshold=-45, distance=5, prominence=10):  # if very noisy signal prominence should be set to high, prominence be always +ve
        super().__init__()
        self.setWindowTitle("Diagonistic Utility")
        self.setGeometry(100, 100, 1800, 1000)  # Set window size

        self.rcv_udp_object = rcv_udp_object
        
        # Set the parameters
        self.frames = frames
        self.fps = fps
        self.threshold = threshold
        self.distance = distance
        self.prominence = prominence

        self.running = True
        
        self.create_widgets()

    def create_widgets(self):
        # Set up the window properties
        self.setWindowTitle('Utility')
        self.setGeometry(50, 50, 1500, 700)  # x, y, width, height
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////
        # Create and configure the button
        self.bind_button = QPushButton('Run', self)
        self.bind_button.clicked.connect(self.start_communication)
        self.bind_button.setStyleSheet("background-color: green;font-size: 20px;")
        self.bind_button.setGeometry(30, 233, 100, 50)

        # Create and configure the button
        self.stop_button = QPushButton('STOP', self)
        self.stop_button.clicked.connect(self.stop_app)
        self.stop_button.setStyleSheet("background-color: pink;font-size: 20px;")
        self.stop_button.setGeometry(200, 233, 100, 50)

# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////
        self.groupBoxForGraph = QGroupBox(self)
        self.groupBoxForGraph.setGeometry(319, 46, 1004, 554)

        # Set a border around the QGroupBox using style sheets
        self.groupBoxForGraph.setStyleSheet(
            "QGroupBox {"
            "   border: 2px solid black;"  # Border width and color
            "   border-radius: 5px;"        # Rounded corners (optional)
            "   padding: 5px;"             # Space between the border and the content
            "}"
        )
        self.LiveGraphText = QLabel("FFT", self)
        self.LiveGraphText.setStyleSheet("background-color: grey; font-size: 25px;")  # Set background color to white
        self.LiveGraphText.setAlignment(Qt.AlignCenter) 
        self.LiveGraphText.setGeometry(322, 50, 998, 40)

        # Create the figure and axes
        self.fig, self.ax = plt.subplots() 
        self.ax.grid(True)
        self.canvas = FigureCanvas(self.fig)  # Create a canvas to hold the figure
        self.canvas.setGeometry(2, 48, 1000, 500)
        self.canvas.setParent(self.groupBoxForGraph)

        
        # Create the lines and texts for scope data
        self.line_scope, = self.ax.plot([], [], lw=1.5, color='g', label='G')  # Blue line for fft data
        self.peak_lines_scope, = self.ax.plot([], [], 'ro')  # Red dots for peaks
        self.peak_texts_scope = []

        #self.ax.set_xlim(0, data.shape[1])
        #self.ax.set_ylim(np.min(data.values), np.max(data.values)+10000)
        
        self.title = self.ax.text(0.5, 0.94, "", bbox={'facecolor': 'w', 'alpha': 0.5, 'pad': 5},
                                       transform=self.ax.transAxes, ha="center")
        self.frame_text = self.ax.text(0.9, 0.9, "", bbox={'facecolor': 'w', 'alpha': 0.5, 'pad': 5},
                                       transform=self.ax.transAxes, ha="center")
        
        self.x_values = np.arange(-255, 257) * (50000 / 8192)
        # self.ax.set_xlim(np.min(self.x_values), np.max(self.x_values))
        self.ax.set_xlim(self.x_values[0], self.x_values[-1])
        self.ax.set_ylim(-80, 10)

        
    def start_communication(self):
        # Create the animation
        self.anim = FuncAnimation(self.fig, self.update_animation, init_func=self.init_animation, frames=self.frames, interval=1000/self.fps, blit=True)

    def stop_app(self):
        self.running = False
        self.anim.event_source.stop()


    def find_peaks_in_row(self, row):
        peaks, peak_properties = find_peaks(row, height=self.threshold, 
                                            distance=self.distance, 
                                            prominence=self.prominence)  # peaks -> array : indices of the local maxima
        return peaks, peak_properties

    def init_animation(self):
        self.line_scope.set_data([], [])
        self.peak_lines_scope.set_data([], [])
        # Clear previous peak texts
        for text in self.peak_texts_scope:
            text.set_visible(False)
        self.peak_texts_scope.clear()

        self.title.set_text("")
        self.frame_text.set_text("")
        return self.line_scope, self.peak_lines_scope, *self.peak_texts_scope, self.title, self.frame_text       

    def update_animation(self, i):
        # Process the data
        data, data_size = self.rcv_udp_object.receive_scan_data()
        if data_size > 0:
            scope_data = self.rcv_udp_object.parse_scan_data() 
            print(','.join(map(str, scope_data)))

            # print(hex(scope_data[0]), scope_data[1], scope_data[2])
            self.packet_no = 1
            scope_data = scope_data[4:]  # 
            print(f"Size of the samples: {len(scope_data)}")

            scope_data = np.array(scope_data, dtype=np.float64)
            print(scope_data)  

            # -------------- Part after this is same  ---------------
            peaks_scope_locations, peak_properties_G = self.find_peaks_in_row(scope_data)
            self.line_scope.set_data(np.arange(-(512 // 2 - 1), 512 // 2 + 1) * (50000 / 8192), scope_data)
            print('peaks_scope_locations :', peaks_scope_locations)
            self.peak_lines_scope.set_data(self.x_values[peaks_scope_locations], scope_data[peaks_scope_locations])            

            # Update peak texts
            for text in self.peak_texts_scope:
                text.set_visible(False)
            self.peak_texts_scope.clear()

            for frequency in peaks_scope_locations:
                magnitude = scope_data[frequency].round().astype(int)
                peak_text = self.ax.text(frequency, magnitude,
                                        f'magnitude={magnitude}\n'
                                            f'frequency={frequency}\n',
                                            color='black',
                                            fontsize=10, ha='center')
                self.peak_texts_scope.append(peak_text)

        # self.title.set_text(f"Row: {i + 1}")
        self.title.set_text(f"Packet No: {self.packet_no}")
        self.packet_no += 1
        self.frame_text.set_text(f"Frame: {i + 1}")
        return self.line_scope, self.peak_lines_scope, *self.peak_texts_scope, self.title, self.frame_text
            


if __name__ == "__main__":
    rcv_udp_object = recieve_scan_UDP('0.0.0.0', 9238)  

    scanInterval = 20
    fps = 1000/scanInterval
    durationOfRunInSecs = 600

    frames = int(durationOfRunInSecs * fps)

    app = QApplication(sys.argv)
    window = MainWindow(rcv_udp_object)
    window.show()
    sys.exit(app.exec_())


# Imports
import socket
import select
import struct
import time
import sys
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.animation import FuncAnimation

from scipy.signal import find_peaks  
from scipy.signal import savgol_filter

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGroupBox, QPushButton


# Constants
ADC_LEAST_COUNT = 5/(2**16)  
SAMPLING_FREQ = 50 # in KHz
SAMPLING_RATE = 1/SAMPLING_FREQ # in Sec


class RECEIVE_UDP_CLASS:
    
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

    def receive_data(self):
        
        # Use select to check if data is available
        readable, _, _ = select.select([self.sock], [], [], 0)

        if self.sock in readable:
            try:
                # Attempt to receive data
                self.data, self.addr = self.sock.recvfrom(2002)  # Buffer size is 2002 bytes
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

    def unpack_data(self):
        # Unpack samples of 2 bytes each (unsigned short)
        self.samples = struct.unpack('1001H', self.data)
        return self.samples


class MainWindow(QMainWindow):
    def __init__(self, receiveUDPClassObject_A, receiveUDPClassObject_B, frames=60, fps=50, threshold=20000, distance=50, prominence=3000):
        super().__init__()
        self.setWindowTitle("Data Monitoring Utility")
        self.setGeometry(100, 100, 1800, 1000)  # Set window size

        self.receiveUDPClassObject_A, self.receiveUDPClassObject_B = receiveUDPClassObject_A, receiveUDPClassObject_B
        
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
        self.setWindowTitle('ADC-Data Monitoring Utility')
        self.setGeometry(50, 50, 1500, 800)  # x, y, width, height
# //////////////////////////////////////////////////////////////////////////////////////////////////////////////    
        # Create and configure the button
        self.bind_button = QPushButton('Run', self)
        self.bind_button.clicked.connect(self.start_communication)
        self.bind_button.setStyleSheet("background-color: green;font-size: 20px;")
        self.bind_button.setGeometry(450, 620, 200, 80)

        # Create and configure the button
        self.stop_button = QPushButton('STOP', self)
        self.stop_button.clicked.connect(self.stop_app)
        self.stop_button.setStyleSheet("background-color: pink;font-size: 20px;")
        self.stop_button.setGeometry(950, 620, 200, 80)
# ////////////////////////////////////////////////////////////////////////////////////////////////////////////
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
        self.LiveGraphText = QLabel("ADC DATA", self)
        self.LiveGraphText.setStyleSheet("background-color: grey; font-size: 25px;")  # Set background color to white
        self.LiveGraphText.setAlignment(Qt.AlignCenter) 
        self.LiveGraphText.setGeometry(322, 50, 998, 40)

        # Create the figure and axes
        self.fig, self.ax = plt.subplots() 
        self.canvas = FigureCanvas(self.fig)  # Create a canvas to hold the figure
        self.canvas.setGeometry(2, 48, 1000, 500)
        self.canvas.setParent(self.groupBoxForGraph)

        # Create the lines and texts for A
        self.line_A, = self.ax.plot([], [], lw=2, color='gray', label='A')  # Blue line for A data
        self.peak_lines_A, = self.ax.plot([], [], 'ro')  # Red dots for peaks
        self.peak_texts_A = []

        # Create the lines and texts for B
        self.line_B, = self.ax.plot([], [], lw=2, color='y', label='B') # Green line for B data
        self.peak_lines_B, = self.ax.plot([], [], 'ro')  # Red dots for peaks
        self.peak_texts_B = []

        #self.ax.set_xlim(0, data.shape[1])
        #self.ax.set_ylim(np.min(data.values), np.max(data.values)+10000)

        self.title = self.ax.text(0.5, 0.94, "", bbox={'facecolor': 'w', 'alpha': 0.5, 'pad': 5},
                                       transform=self.ax.transAxes, ha="center")
        self.frame_text = self.ax.text(0.9, 0.9, "", bbox={'facecolor': 'w', 'alpha': 0.5, 'pad': 5},
                                       transform=self.ax.transAxes, ha="center")
        
        self.ax.set_xlim(0, 1000)
        self.ax.set_ylim(20000, 80000)

        
    def start_communication(self):
        # Create the animation
        self.anim = FuncAnimation(self.fig, self.update_animation, init_func=self.init_animation, frames=self.frames, interval=1000/self.fps, blit=True)
        # self.bind_button.clicked.disconnect(self.start_communication)


    def stop_app(self):
        self.running = False
        self.anim.event_source.stop()

    def find_peaks_in_row(self, row):
        peak_locations, peak_properties = find_peaks(row, height=self.threshold, 
                                            distance=self.distance, 
                                            prominence=self.prominence)  # peak_locations -> array : indices of the local maxima
        return peak_locations, peak_properties

    def init_animation(self):
        self.line_A.set_data([], [])
        self.peak_lines_A.set_data([], [])
        # Clear previous peak texts
        for text in self.peak_texts_A:
            text.set_visible(False)
        self.peak_texts_A.clear()

        self.line_B.set_data([], [])
        self.peak_lines_B.set_data([], [])
        # Clear previous peak texts
        for text in self.peak_texts_B:
            text.set_visible(False)
        self.peak_texts_B.clear()

        self.title.set_text("")
        self.frame_text.set_text("")
        return self.line_A, self.peak_lines_A, *self.peak_texts_A, self.line_B, self.peak_lines_B, *self.peak_texts_B, self.title, self.frame_text       

    def update_animation(self, i):
        # Process the A data
        data, data_size = self.receiveUDPClassObject_A.receive_data()
        if data_size > 0:
            samples_A = self.receiveUDPClassObject_A.unpack_data()  # 2002 bytes
            # print(','.join(map(str, samples_A)))

            # print(hex(samples_A[0]), samples_A[1], samples_A[2])
            self.packet_no = samples_A[0]
            samples_A = samples_A[1:]  # skip 2 bytes
            print(f"Size of the samples: {len(samples_A)}")

            # Apply Savitzky-Golay filter on received data
            row_A = savgol_filter(samples_A, 41, 3)
            # print(row_A.dtype)    # float64
            # print(row_A)

            #row = self.data.iloc[i].values
            peak_locations_A, peak_properties_A = self.find_peaks_in_row(row_A)
            self.line_A.set_data(np.arange(len(row_A)), row_A)
            # print(peak_locations_A, row_A[peak_locations_A])
            self.peak_lines_A.set_data(peak_locations_A, row_A[peak_locations_A])            

            # Update peak texts
            for text in self.peak_texts_A:
                text.set_visible(False)
            self.peak_texts_A.clear()

            for peak_location_A in peak_locations_A:
                peak_value = row_A[peak_location_A].round().astype(int)
                peak_height = peak_properties_A['prominences'][list(peak_locations_A).index(peak_location_A)].round().astype(int)
                peak_text = self.ax.text(peak_location_A, peak_value+1000,
                                        f'index = {peak_location_A}\n'
                                            f'time = {round(peak_location_A * SAMPLING_RATE, 3)} mSec\n'
                                            f'peakValue = {peak_value}\n'
                                            f'peakValueChange = {round(peak_value * ADC_LEAST_COUNT, 3)} V\n'
                                            f'prominenceChange = {round(peak_height * ADC_LEAST_COUNT, 3)} V',
                                            color='darkviolet',
                                            fontsize=8, ha='center')
                self.peak_texts_A.append(peak_text)

        # Process the B data
        data, data_size = self.receiveUDPClassObject_B.receive_data()
        if data_size > 0:
            samples_B = self.receiveUDPClassObject_B.unpack_data()  # 2002 bytes
            # print(','.join(map(str, samples_B)))

            # print(hex(samples_B[0]), samples_B[1], samples_B[2])
            self.packet_no = samples_B[0]
            samples_B = samples_B[1:]  # skip 2 bytes
            print(f"Size of the samples: {len(samples_B)}")

            # Apply Savitzky-Golay filter on received data
            row_B = savgol_filter(samples_B, 41, 3)
        
            peak_locations_B, peak_properties_B = self.find_peaks_in_row(row_B)
            self.line_B.set_data(np.arange(len(row_B)), row_B)
            # print(peak_locations_B, row_A[peak_locations_B])
            self.peak_lines_B.set_data(peak_locations_B, row_B[peak_locations_B])            

            # Update peak texts
            for text in self.peak_texts_B:
                text.set_visible(False)
            self.peak_texts_B.clear()

            for peak_location_B in peak_locations_B:
                peak_value = row_B[peak_location_B].round().astype(int)
                peak_height = peak_properties_B['prominences'][list(peak_locations_B).index(peak_location_B)].round().astype(int)
                peak_text = self.ax.text(peak_location_B, peak_value+1000,
                                        f'index = {peak_location_B}\n'
                                            f'time = {round(peak_location_B * SAMPLING_RATE, 3)} mSec\n'
                                            f'peakValue = {peak_value}\n'
                                            f'peakValueChange = {round(peak_value * ADC_LEAST_COUNT, 3)} V\n'
                                            f'prominenceChange = {round(peak_height * ADC_LEAST_COUNT, 3)} V',
                                            color='black',
                                            fontsize=8, ha='center')
                self.peak_texts_B.append(peak_text)

        self.title.set_text(f"Packet No: {self.packet_no}")
        self.frame_text.set_text(f"Frame: {i + 1}")
        return self.line_A, self.peak_lines_A, *self.peak_texts_A, self.line_B, self.peak_lines_B, *self.peak_texts_B, self.title, self.frame_text
            

if __name__ == "__main__":
    receiveUDPClassObject_A, receiveUDPClassObject_B = RECEIVE_UDP_CLASS('0.0.0.0', 30000), RECEIVE_UDP_CLASS('0.0.0.0', 30001)   # object

    scanInterval = 25
    fps = 1000/scanInterval
    durationOfRunInSecs = 500

    frames = int(durationOfRunInSecs * fps)

    app = QApplication(sys.argv)
    window = MainWindow(receiveUDPClassObject_A, receiveUDPClassObject_B, frames, fps)
    window.show()
    sys.exit(app.exec_())



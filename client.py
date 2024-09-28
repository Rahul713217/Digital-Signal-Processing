import struct 
import socket
import time
import numpy as np 
import pandas as pd
from scipy.signal import savgol_filter

IP_ADDRESS = '127.0.0.1'
PORT_A = 30000
PORT_B = 30001

def applySavitzkyGolayFilter(input_df, window_length=41, poly_order=3):
    input_df = input_df.transpose()
    input_df = input_df.apply(lambda x: savgol_filter(x, window_length, poly_order))
    input_df = input_df.transpose()
    return input_df

def averageScans(input_df, number_of_scans_to_average=8):
    input_df = input_df.groupby(np.arange(len(input_df))//number_of_scans_to_average).mean()
    return input_df

def read_ADC_data_in_chunks(file_path_A, file_path_B, chunk_size=8):
    # Create iterators for both files
    iterator_A = pd.read_csv(file_path_A, chunksize=chunk_size)
    iterator_B = pd.read_csv(file_path_B, chunksize=chunk_size)

    while True:
        try:
            chunk_A = next(iterator_A)
            chunk_B = next(iterator_B)
            yield chunk_A, chunk_B  # Yield chunks from both files
        except StopIteration:
            break  # Exit the loop when either iterator is exhausted


class SEND_UDP_CLASS:
    def __init__(self, ip_address, port_A, port_B, input_df_A, input_df_B) -> None:
        self.ip_address = ip_address
        self.port_G = port_A
        self.port_H = port_B
        self.input_df_G = input_df_A
        self.input_df_H = input_df_B
        self.sock = self.init_UDP_COMM()
        
    def init_UDP_COMM(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
        return sock

    def pack_data(self,input_df, i=0):
        packed_data = struct.pack('<H' + 'H' * 1000, i+1, *input_df)  
        return packed_data

    def send_data(self, i):    
        try:
            packed_data_G, packed_data_H = self.pack_data(self.input_df_G, i), self.pack_data(self.input_df_H, i)
            self.sock.sendto(packed_data_G, (self.ip_address, self.port_G))  
            self.sock.sendto(packed_data_H, (self.ip_address, self.port_H))  
            print(f'sent {len(packed_data_G)} bytes of data to {self.ip_address}')  

        except KeyboardInterrupt as k:
            print(str(k))
        except Exception as e:
            print(str(e))
        finally:
            self.sock.close()


def main():
    file_path_A, file_path_B = 'Data/a.csv', 'Data/b.csv'

    while True:
        i = 0
        for input_df_A, input_df_B in read_ADC_data_in_chunks(file_path_A, file_path_B, chunk_size=32):
            input_df_A, input_df_B = applySavitzkyGolayFilter(input_df_A), applySavitzkyGolayFilter(input_df_B)
            input_df_A, input_df_B = averageScans(input_df_A, 32), averageScans(input_df_B, 32)

            input_df_A, input_df_B = input_df_A.astype(np.uint16), input_df_B.astype(np.uint16)
            input_df_A, input_df_B = input_df_A.iloc[0].to_numpy(), input_df_B.iloc[0].to_numpy()
            # print(input_df)
            
            sendUDPClassObject = SEND_UDP_CLASS(IP_ADDRESS, PORT_A, PORT_B, input_df_A, input_df_B)
            sendUDPClassObject.send_data(i)
            
            i += 1
            time.sleep(.8)


if __name__ == '__main__':
    main()
    
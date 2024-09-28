# ADC-Data-Monitoring

This project is designed for monitoring ADC (Analog-to-Digital Converter) data on a Graphical User Interface (GUI).

Ensure your CSV files contain the necessary data, or that you have a process running that writes data to the CSV files located in the `Data` folder.

To install the necessary modules and libraries, run the following command:

## `pip3 install pyqt5 matplotlib scipy`

You need to modify `IP_ADDRESS` as per your need. Here I used localhost, same device will send the data and receive it.

In the project directory, open two separate terminal.

You'll need to run both the server and the client in separate terminals.

Run the Server:

In the first terminal, start the server:

## `python3 server.py`

Run the Client:

In the second terminal, start the client:

## `python3 client.py`

After this, press the `Run` button on the GUI for data observation. The `Run` button will start the animation.

Feel free to modify any sections further to suit your project's specifics!


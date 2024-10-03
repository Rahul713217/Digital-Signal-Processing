# UDP COMMUNICATION 

# PS 10/100/1000BASE-T via MIO v2022.2

## **Design Summary**

This project utilizes GEM3 configured for RGMII via MIO. This has been routed to the on-board TI DP83867 PHY found on the ZCU102.

---

## **Required Hardware**
- ZCU102
---

zcu102 board act as client 

zcu102 board will send data on the ethernet (ps_mio_eth_1g) on PS side at rate 1ghz

## **Required Software**
 - Vitis v2022.2

I made one GUI in PyQt that receives the data and plot the graph or animation using the data. 

Can use this project for analyzing real time signal data afterFast Fourier Transform (FFT).

Here I provide the signal's data after fft in one array, but we can write the fft code and directly provide the signal's data as parameter in the fft function and show the animation in real time for further analysis.

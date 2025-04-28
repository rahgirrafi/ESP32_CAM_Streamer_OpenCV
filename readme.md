# ESP32 Cam Streamer OpenCV

Foobar is a Python library for dealing with word pluralization.

## Installation

Clone the repository

```bash
git clone https://github.com/rahgirrafi/ESP32_CAM_Streamer_OpenCV.git -b stream
```

## Repository Details
The firmware for EPS32 was developed using platformio. You can find all the program files in the src directory and all the header files in the include directory. If you want to use the firmwire in Arduino IDE, then just copy all the program files and header files in a Arduino Project DIrectory. You may have to remove the #include <Arduino.h> tag in that case.

## Project Details
Here the ESP32 CAM acts as a TCP Client and a host computer acts as a TCP server. The ESP32 CAM only captures the image and sends it to a Local Server through TCP protocol. A host computer that is running the Server code (you can find it in the python directory) will receive the image and load it in openCV. After thatyou can use the image normally and do all the openCV operations with it.

## Dependencies
The server depends on:

-socket

-opencv-python

-numpy


## How to use
Your host computer and the ESP32 CAM must be "CONNECTED TO THE SAME LOCAL NETWORK" i.e. same router, same switch etc. This code will not send data over internet.It will only work with LAN network.



In the Firmware code, make the following changes.

**SSID:** Replace with your own Wifi Network Name.

**Password:** Replace it with your own Wifi Password.

**Server IP:** Find the IP adress of your Host Computer. In Linux you can use the following cammand:
```bash
hostname -I
```
**ServerPort (Optional)** : You may not need to change it. But just in case, if your post 8000 is being used for some other task, you may get an error. In that case, just assign some other random post numbers. Carefully change the port number in both the firmware code and the server code (python). The post has to be the same for the both device to communicate with each other.


## Issue
If you face any problem using the code, open an issue. I will try to solve it.
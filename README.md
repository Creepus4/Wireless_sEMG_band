# Wireless sEMG band

This GitHub repository provides the code used to connect to, plot, and identify movements for the armband developed during a bachelor's thesis. It includes the ESP32 code used for wireless transmission and sampling on the ESP32-S3-DevKitC, as well as 64-bit x86-targeted code for signal processing, plotting, and movement classification. Note that the movement classification may not be reliable.

![Alt text](pictures/ch2_GUI.png)

# Usage

To use this code, you need two ESP32 devices with wireless communication capabilities and a Windows computer running Windows 10 or later (other microcontrollers, operating systems, or versions may work, but they have not been tested).

Compile the C++ code in the "ESP32Code" folder for the ESP32 devices, and upload the receiver code to the ESP32 connected via USB to the Windows computer. The transmitter code should be uploaded to the ESP32 connected to a low-pass filtered EMG signal.

The sample rate, number of EMG channels, and ESP-NOW packet size can be changed through the macros at the top of the transmitter.cpp file.

This should allow the EMG signal to be sampled and transmitted to the computer, where it can be read by the operating system.

For the computer side, use the code in the GUI folder. The config.py file contains all configurable parameters used to customize the plot. The wrapper.py file acts as an interface between the DLL files and Python by providing Python functions. You need to specify the file paths to the two DLL files in order for the program to work.

The GUI folder also contains precompiled DLL files. However, if you want to compile them yourself, the C++ source code can be found in the dllSourceCode folder.

# -- add about the main application--

The Esp32Test folder contains the test code used on the ESP32 devices during the bachelor's thesis to evaluate packet loss, latency, and the maximum EMG signal amplitude.

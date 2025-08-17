# 🚶 Smart Pedestrian Crossing System

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python)](https://www.python.org/) [![OpenCV](https://img.shields.io/badge/OpenCV-4.12-5C3EE8?style=for-the-badge&logo=opencv)](https://opencv.org/) [![Arduino IDE](https://img.shields.io/badge/Arduino-ESP8266-00979D?style=for-the-badge&logo=arduino)](https://www.arduino.cc/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)

A complete system that leverages the YOLOv8 object detection model to count the number of people waiting to cross a street and intelligently controls a physical pedestrian crossing signal (Red/Green LEDs) connected to an ESP8266. The communication between the computer vision script and the microcontroller is handled seamlessly over a serial connection.

---

## Table of Contents

- [About The Project](#about-the-project)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Hardware Setup & Circuit](#hardware-setup--circuit)
  - [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [Code Structure](#code-structure)
- [License](#license)

---

## About The Project

This project bridges the gap between high-level computer vision and physical hardware control. It provides a practical solution for automating pedestrian management systems, such as activating crosswalk signals on demand or managing foot traffic flow at building entrances.

The system uses a webcam or video file as input.A Python script running the powerful YOLOv8 model detects and tracks individuals within a user-defined **Region of Interest (ROI)**.The real-time count of people is then sent to an ESP8266 microcontroller, which executes a timer-based logic to manage a red ("Don't Walk") and a green ("Walk") LED. The timer's duration dynamically adjusts based on the number of people detected, making the system efficient and responsive.For example, a larger group of people will get the "Walk" signal faster than a single individual.

---

## Key Features

- **👀 Real-Time Person Detection**: Utilizes the state-of-the-art **YOLOv8n model** for fast and accurate detection and tracking of people.
- **🖱️ Interactive ROI Selection**: An easy-to-use interface allows you to draw a detection zone directly on the video feed, which is then saved for future use.
- **🔌 Seamless Serial Communication**: Reliably transmits the person count from the Python script to the ESP8266 using the `PySerial` library.
- **💡 Dynamic Timer Logic**: The ESP8266 code implements a smart timer that adjusts its duration based on the number of people detected—more people result in a shorter wait time for the "Walk" signal.
- **⚙️ Standalone & Robust**: The system is designed to run continuously.The Python script handles video stream errors, and the ESP8266 manages the LED states independently once it receives a count.
- **🔧 Easy to Test**: Includes multiple helper scripts for isolated component testing.
    - `esp8266check_code.py`: Tests the serial communication with the ESP8266.
    - `webcamtest.py`: Verifies basic camera functionality with OpenCV.
    - `test2.py`: Confirms that the YOLOv8 model is installed and running correctly on the webcam feed.
---

## System Architecture

The system's workflow creates a one-way data pipeline from visual input to physical output.

1.  **Video Input**: The Python script captures video from a webcam or a file using **OpenCV**.
2.  **ROI Definition**: On the first run, the user draws a rectangle on a frame to define the waiting area where people should be counted.This ROI is saved in a `roi.json` file.
3.  **Detection & Counting**: For each frame, the **YOLOv8 model** processes the video to detect and track individuals.The script counts only those whose bounding boxes have a significant overlap (>=50%) with the defined ROI.
4.  **Serial Transmission**: Whenever the number of people in the zone changes, the Python script sends the new count as a string to the ESP8266 over the specified serial (COM) port.
5.  **Hardware Control**:
    * The **ESP8266** continuously listens for incoming serial data.
    * If `personCount > 0`, it turns on the **RED LED** (signifying "Don't Walk") and starts a timer.The timer's duration is inversely proportional to the `personCount` (e.g., 1 person = 90s, 4 people = 30s).
    * When the timer expires, it turns off the RED LED and turns on the **GREEN LED** (signifying "Walk").
    * The system fully resets (both LEDs off) only when it receives a `personCount` of `0`.

---

## Getting Started

Follow these steps to get the project running on your own hardware.

### Prerequisites

#### Hardware
* An ESP8266-based board (NodeMCU is used in the example) 
* 1x Red LED 
* 1x Green LED 
* Breadboard and connecting wires (Jumper cables)
* A webcam

#### Software
* [Python](https://www.python.org/downloads/) (3.8 or newer)
* [Arduino IDE](https://www.arduino.cc/en/software) with the ESP8266 board manager installed.
* All Python packages listed in `requirements.txt`.

---

### Hardware Setup & Circuit



Wire the components according to the image provided and the pin definitions in the code.

**Connect your components as shown in the table below:**

| Component Pin   | Pin (ESP8266) | Purpose                |
|---------------|---------------|------------------------|
| Red LED Anode   | D1 (GPIO 5)   | Red Light (Don't Walk) |
| Green LED Anode | D2 (GPIO 4)   | Green Light (Walk)     |
| Red LED Cathode | GND           | Ground                 |
| Green LED Cathode| GND          | Ground                 |

*Note: The circuit diagram and an image of the physical setup are available in the `media` folder for reference.*

---

### Installation & Setup

1.  **Clone the Repository**
    ```sh
    git clone [https://github.com/AnshuMohanan/-Smart-Traffic-Light-System.git](https://github.com/AnshuMohanan/-Smart-Traffic-Light-System.git)
    cd -Smart-Traffic-Light-System
    ```

2.  **ESP8266 Setup**
    1.  Open `traffic_light.ino` in the Arduino IDE.
    2.  Go to **Tools > Board** and select your ESP8266 board (e.g., "NodeMCU 1.0 (ESP-12E Module)").
    3.  Select the correct COM port under **Tools > Port**.
    4.  Click the "Upload" button to flash the code to the board.

3.  **Python Environment Setup**
    1.  It is highly recommended to create a virtual environment:
        ```sh
        python -m venv venv
        source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
        ```
    2.  Install all the required packages:
        ```sh
        pip install -r requirements.txt
        ```

---

## Usage

1.  **Connect the Hardware**: Plug the ESP8266 into your computer via USB. Note the COM port it is assigned (e.g., `COM3` on Windows, `/dev/ttyUSB0` on Linux). You can find this in the Arduino IDE under **Tools > Port**.

2.  **Run the Main Script**: Open your terminal, navigate to the project directory, and run `FINALCODE_C_test.py` with the required arguments.
    * `--source`: Use `'0'` for your primary webcam or provide a path to a video file.
    * `--port`: The COM port your ESP8266 is connected to.

    **Example for Webcam:**
    ```sh
    python FINALCODE_C_test.py --source 0 --port COM3
    ```

    **Example for a Video File:**
    ```sh
    python FINALCODE_C_test.py --source "path/to/your/video.mp4" --port COM3
    ```

3.  **Define the ROI**:
    * If this is your first time running the script, a window titled "Select ROI" will appear.
    * **Click and drag** your mouse to draw a rectangle over the area you want to monitor.
    * Press the **`c`** key to confirm and save the ROI.The detection will then begin.
    * On subsequent runs, the script will ask if you want to **(U)se** the existing ROI or **(D)efine** a new one.

4.  **Observe the System**:
    * A window will show the live video feed with bounding boxes around detected people in the zone and a counter.
    * The LEDs on your breadboard will change according to the logic described in the **System Architecture**.
    * The terminal will print messages indicating the connection status and the counts being sent to the ESP8266.
    * Press **`q`** to stop the program.This will also send a `0` to the ESP8266 to reset the lights.
  
5.  **🎥 Demonstration**:

    * [▶️ Watch a video of the main program in action!](https://your-video-link-here.com)
    * [▶️ Watch a video of the arduino hardware in action!](https://drive.google.com/file/d/1COnaJQUGI8DQDU2dDlQMOfPljmzT9wij/view?usp=sharing)


---

## Code Structure

The project contains a few key files that work together:

-   `FINALCODE_C_test.py`: The main Python script that handles everything on the computer side: video capture, ROI selection, object detection with YOLO, and serial communication.
-   `traffic_light.ino`: The Arduino C++ code for the ESP8266.It listens for serial input and controls the RED and GREEN LEDs based on the received person count and its internal timer logic.
-   `requirements.txt`: A list of all Python dependencies required to run the detection script.

---

## License

This project is distributed under the MIT License. See the `LICENSE` file for more information.

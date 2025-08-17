import serial
import time

# --- Main Script ---

# 1. Get the serial port from the user
try:
    port = input("Enter the ESP8266 serial port (e.g., COM3 or /dev/ttyUSB0): ")
    baud_rate = 115200
except KeyboardInterrupt:
    print("\nProgram cancelled by user.")
    exit()


# 2. Try to connect to the port
serial_connection = None
try:
    print(f"Attempting to connect to {port} at {baud_rate} bps...")
    # Establish the connection
    serial_connection = serial.Serial(port, baud_rate, timeout=1)
    # Wait 2 seconds for the ESP8266 to reset and establish connection
    time.sleep(2)
    print("✅ Connection successful. Ready to send numbers.")
    print("-------------------------------------------------")

    # 3. Loop forever to get user input
    while True:
        # Get a number from the user
        user_input = input("Enter a number to send (or type 'quit' to exit): ")

        # Check if the user wants to quit
        if user_input.lower() == 'quit':
            print("Exiting program.")
            break

        # Check if the input is a valid whole number
        if not user_input.isdigit():
            print("❌ Invalid input. Please enter a whole number.")
            continue # Go to the next loop iteration

        # Format the message by adding a newline character.
        # This is CRUCIAL for the ESP8266's Serial.readStringUntil('\n') to work.
        message_to_send = user_input + '\n'

        # Send the string, encoded as bytes
        serial_connection.write(message_to_send.encode())
        print(f"Sent: '{user_input}'")


except serial.SerialException as e:
    print(f"❌ Error: Could not connect to the port '{port}'.")
    print(f"   Please check the port name and ensure no other program (like the Arduino Serial Monitor) is using it.")
    print(f"   Details: {e}")

except KeyboardInterrupt:
    print("\nProgram interrupted by user.")

finally:
    # 4. This block runs whether there was an error or not.
    # It ensures the serial connection is properly closed.
    if serial_connection and serial_connection.is_open:
        print("Sending '0' to reset the ESP and closing connection...")
        # Send a 0 to reset the ESP's state before closing
        serial_connection.write(b'0\n')
        serial_connection.close()
        print("Connection closed.")
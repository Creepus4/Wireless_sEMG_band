import serial
import threading
import time

BAUD_RATE = 921600
EXPECTED_BYTES = 194
TOTAL_SAMPLES = 100

totalRuns = 0
times = [0] * TOTAL_SAMPLES
stop_thread = False

ser = serial.Serial(port='COM5', baudrate=BAUD_RATE, timeout=1)
transmitter = serial.Serial(port='COM7', baudrate=BAUD_RATE, timeout=0)

def serial_reader():
    global totalRuns, times, stop_thread
    print("start")

    time.sleep(2)

    ser.reset_input_buffer()

    while totalRuns < TOTAL_SAMPLES:

        startTime = time.perf_counter()
        transmitter.write(b"s")

        while ser.in_waiting < EXPECTED_BYTES: 
            time.sleep(0.001)

            if time.perf_counter() - startTime > 1.0: 
                print ("No response, retrying")
                break

        raw = ser.read(EXPECTED_BYTES)
        elapsed = time.perf_counter() - startTime

        if len(raw) == EXPECTED_BYTES: 
            times[totalRuns] = elapsed
            print(f"Run {totalRuns} Time {elapsed}")

            ser.reset_input_buffer()

            totalRuns +=1

        time.sleep(0.05)

    print(f"Mean time: {1000*sum(times)/TOTAL_SAMPLES} ms")
    print(f"Min time: {1000*min(times)} ms")
    print(f"Max time: {1000*max(times)} ms")

t = threading.Thread(target=serial_reader)
t.start()

while t.is_alive():
    time.sleep(0.1)

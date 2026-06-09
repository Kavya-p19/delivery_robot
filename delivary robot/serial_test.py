import serial
import time

data = serial.Serial(
                  'COM7',
                  baudrate = 9600,
                  parity=serial.PARITY_NONE,
                  stopbits=serial.STOPBITS_ONE,
                  bytesize=serial.EIGHTBITS,                  
                  timeout=1
                  )
time.sleep(2.5)

def Send(msg):
    data.write(str.encode(msg))
    print(f'data {msg} sent...')

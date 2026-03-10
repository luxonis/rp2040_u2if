import time
from rp2040_u2if import RP2040_u2if


dev = RP2040_u2if()
dev.open()

dev.uart_init(115200)       # defaults to UART1

dev.uart_read()             # flush garbage
dev.uart_write(b"hello\n")

data = dev.uart_read()
print(data)

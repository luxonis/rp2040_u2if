import time
from rp2040_u2if import RP2040_u2if

rp2040 = RP2040_u2if()
rp2040.open()

rp2040.uart_set_port(1)
rp2040.uart_configure(115200)

# RX and TX lines should be connected together for this test to work (loopback)
for _ in range(5):
    tx = b"loopback test\r\n"
    rp2040.uart_write(tx)
    rx = rp2040.uart_readline(timeout=1.0)
    print(f"TX: {tx!r} RX: {rx!r} OK: {rx == tx}")
    time.sleep(1.0)

rp2040.uart_deinit()
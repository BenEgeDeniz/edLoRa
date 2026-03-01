# CLI Packet Stream Monitor

The `cli_monitor.py` script included in the `examples/` directory is an immensely powerful debugging tool for monitoring incoming `edLoRa` radio traffic from a local serial device (e.g. an Arduino or ESP32 plugged into your laptop parsing RF LoRa commands via USB).

## Requirements
To use the CLI Stream Monitor, you must install `pyserial`.
```bash
pip install pyserial
```

## Running the Monitor
Run the monitor directly from your command line.

### Basic Serial Monitoring
Point the script directly at your radio's COM Port or `/dev/ttyUSB`:
```bash
python3 examples/cli_monitor.py /dev/ttyUSB0 115200
```
*(Optionally change the baud rate default from `115200` to whatever your hardware employs).*

The monitor natively reads from the byte-stream natively, safely dumps incomplete garbage packets automatically, processes valid CRC headers, un-shifts little-endian integers, and maps the entire byte array to the terminal visually.

### Demo Mode
If you do not currently have a physical radio plugged in, you can run the analyzer in Mock Mode immediately to view the visual layout format.
```bash
python3 examples/cli_monitor.py --demo
```

## Visual Output Format
The monitor builds a dynamic string layout that looks like this:

`[Timestamp] [Sender ID] [MsgType] [Receiver Map] Payload Data`

**Examples:**
```
[2802378780ms] [0x10] [ALTIMETER] [BROADCAST] Altitude: 1500.50m, Velocity: 20.30m/s
[2802379780ms] [0x01] [COMMAND] [TARGETED: 0x10] 'DEPLOY MAIN CHUTE'
[2802380280ms] [0x10] [ACK] [TARGETED: 0x01] Acknowledged Seq: 142
```

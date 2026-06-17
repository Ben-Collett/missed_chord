from contextlib import contextmanager

import serial
import serial.tools.list_ports


def chord_to_list(chord_input: str, chord_output: str) -> tuple[list[int], list[int]]:
    data = bytes.fromhex(chord_input)
    bits = int.from_bytes(data, 'big')
    input_codes = []
    for i in range(12):
        shift = 110 - 10 * i
        code = (bits >> shift) & 0x3FF
        if code != 0:
            input_codes.append(code)
    input_codes = sorted(input_codes + [0] * (12 - len(input_codes)))[:12]
    output_bytes = bytes.fromhex(chord_output)
    output_codes = list(output_bytes)
    return (input_codes, output_codes)


def get_description(device: str) -> str:
    for port in serial.tools.list_ports.comports():
        if port.device == device:
            return port.description
    return ""


def list_chara_devices_with_desc() -> tuple[list[str], list[str]]:
    devices = []
    descriptions = []
    for port in serial.tools.list_ports.comports():
        if "charachorder" in port.description.lower():
            devices.append(port.device)
            descriptions.append(port.description)
    return devices, descriptions


def list_chara_devices() -> list[str]:
    devices = []
    for port in serial.tools.list_ports.comports():
        if "charachorder" in port.description.lower():
            devices.append(port.device)
    return devices


@contextmanager
def open_connection(port: str, timeout: float = 1):
    conn = serial.Serial(port, baudrate=115200, timeout=timeout)
    try:
        yield conn
    finally:
        if conn.is_open:
            conn.close()


def send_command(serial: serial.Serial, command: str) -> str:
    serial.write((command + "\r\n").encode())
    while True:
        line = serial.readline().decode().strip()
        if line:
            return line


def get_chord_count(serial: serial.Serial) -> int:
    response = send_command(serial, "CML C0")
    return int(response.split()[2])


def get_chord_by_index(serial: serial.Serial, index: int) -> tuple[str, str]:
    response = send_command(serial, f"CML C1 {index}")
    parts = response.split()
    return (parts[3], parts[4])


def get_all_chords(serial: serial.Serial) -> list[list[str]]:
    count = get_chord_count(serial)
    chords = []
    for i in range(count):
        chord_hex, phrase_hex = get_chord_by_index(serial, i)
        chords.append([chord_hex, phrase_hex])
    return chords


def hex_chords_to_list(chords: list[list[str]]) -> list[tuple[int, int]]:
    structured_chords = []
    for chord in chords:
        structured_chords.append(chord_to_list(*chord))
    return structured_chords


def chord_backup_map(chords: list[tuple[int, int]]) -> dict:
    return {
        "charaVersion": 1,
        "type": "chords",
        "chords": chords,
    }

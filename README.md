# Missed Chord

A Windows/Linux program designed to work alongside a CharaChorder (or my fuzzy_chips program) when practicing. It monitors your typing and sends a notification when you miss an opportunity to use a chord/chip shortcut and type the text manually instead.



## Disclaimer 
This project has no affiliation with CharaChorder as a company. This project is simply developed and maintained by someone who is trying to get good at using a CharaChorder.

## Notification Modes

Missed Chord supports two notification backends:

### Qt Mode
- Default on **Windows**
- Default on **Linux X11**
- Uses a Qt window for notifications
- ❌ Does not work on Wayland

### Notify Mode
- Default on **Linux**
- Optional on **Windows/macOS** and **X11**
- Uses `notify-send` via D-Bus
- Requires a notification daemon

These will be referred to as qt mode and notify mode throughout the rest of this README.
## Dependencies
python 3

if you want to use qt mode:
- pyside6

if you want to update the chords from the device without manually exporting from the device manager:
- pyserial
     
You can run 
```bash
pip install pyside6
pip install pyserial
```
  
On Linux, as well as other platforms if you want to use notify mode instead of qt mode
- **notify-send** - Desktop notification utility
- **Notification daemon** - Such as:
  - dunst
  - SwatNotificationCenter
  - Or any other D-Bus compatible notification service


## Installation

1. *LINUX ONLY* Install system dependencies (example for Debian/Ubuntu):
```bash
sudo apt-get install make gcc libxkbcommon-dev python3-evdev libnotify dunst
```
1. Clone or download this repository
```bash
git clone https://github.com/Ben-Collett/missed_chord
```

## Configuration
You can define a `config.toml` file in the project directory or in your systems configuration path

On linux this will usually be `~/.config/missed_chord/`

On Windows it's usually `C:\Users\<username>\AppData\Roaming\missed_chord\`

You can see an example configuration file with an explanation for each setting available to you in [example_configs/config.toml](example_configs/config.toml)
##  Config for Charachorders
There are three ways to get the chords from your charachorder to where the program can read it.
1) Run the program with no `chords.json` present while a CharaChorder is connected. The device is autodetected and chords are loaded live from it on startup. This is slower than loading from a file. If multiple devices are detected, you will be prompted to select one. If none are detected, chords are set to empty.
2) Run `python main.py -u` with your charachorder connected through USB. This requires `pyserial` and will generate a `chords.json` file from the device.
3) Export your CharaChorder chord library:
   - Open the CharaChorder Manager application
   - Export your chord library for backup
   - Copy the exported json file to the project directory or wherever your `config.toml` is
   - Rename it to `chords.json`

When you reload the config, chords are loaded from `chords.json` if available. If not, it falls back to the device selected during startup. If no device was selected and exactly one is connected, it is used. If none are connected, chords are set to empty.
## Chip Config

If you are using fuzzy_chips' OS level config directory then it will automatically source it's chips from there if not simply copy your config to the same directory as your `config.toml` for this project and rename it to `chips.toml`
## Usage

**Important:** On wayland(or X11 in notify mode) this program must be run in user mode, not with `sudo`. The script will prompt you for your admin password when needed to access keyboard input on Wayland.

1. Run the program:
```bash
#on Linux in notify mode and Windows
python main.py
#on X11 in qt mode
sudo python main.py
```


The program will now monitor your typing and send notifications when you miss chord/chip opportunities.

### Command Line Flags

| Flag | Description |
|------|-------------|
| `-h`, `--help` | Show help message and all cli flags and exits |
| `-u`, `--update-chords` | Update chord backup from a connected CharaChorder device (requires `pyserial`) |
| `-c`, `--force-chara` | Force CharaChorder mode, ignoring the mode set in config |
| `-f`, `--force-fuzzy` | Force fuzzy chips mode, ignoring the mode set in config |

### Update chords from device


## How It Works

The program monitors keyboard events and detects when you:
1. Type the trigger for a chord (which gets deleted)
2. Then type the text output of that chord manually

When this pattern is detected, it sends a notification showing what chord you could have used instead.

## Limitations and Edge Cases

1. **CharaChorder Mode**: This program only works with CharaChorder's default mode, **not** in "spurrging mode".

1. **Detection Method**: The program relies on the trigger being deleted in order to detect a chord. This means the detection works by observing when the chord trigger is typed and then removed.

1. **Edge Case**: Typing a chord trigger, deleting it manually, and then typing the chord output will be interpreted as a successful chord.


## D-Bus Requirement(notify-mode only)

It's important to note that the script needs to run in user mode (not with `sudo`) because:
- The program needs admin privileges to read keyboard input on Wayland
- However, it also needs access to D-Bus to send notifications
- Running as root (`sudo python main.py`) will prevent the notification service from working because D-Bus is not accessible to root processes

The program handles this by running as a regular user and only using `sudo` for the specific keyboard input access subprocess.

## Troubleshooting

- **Notifications not appearing**: Make sure you have a notification daemon running (like dunst or SwatNotificationCenter)
- **Permission denied**: Make sure you're running the program as a regular user (not with `sudo`) and enter the password when prompted
- **chords.json not found**: Ensure you've exported your chord library from CharaChorder Manager and placed it in the project directory as `chords.json`

## Acknowledgments

This project vendors a keyboard module from
[Ben-Collett/py_keys](https://github.com/Ben-Collett/py_keys), a fork I
maintain of the original
[boppreh/keyboard](https://github.com/boppreh/keyboard) library.

The `keyboard` project, created by boppreh, enabled reliable cross-platform
keyboard event handling and text injection, and forms a critical foundation
for this software. Without it this program would have stayed Linux only, like it originally was. 

## Roadmap
- Read chords directly from CharaChorder when available
- Add a setting to listen to the timing of chords to reduce false negatives
- Add video examples to the readme.
- MacOS support, (requires changes in py_keys which I lack a Mac to do)

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details



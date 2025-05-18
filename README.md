# Windows RTSP Scanner

A Windows-compatible utility for scanning networks to discover RTSP camera streams.

## Overview

This tool helps you find RTSP cameras on your network by:
1. Scanning IP ranges for open RTSP ports
2. Testing discovered endpoints with common RTSP paths
3. Verifying working streams by capturing a frame

Unlike other RTSP scanners, this tool was designed specifically to work on Windows without requiring any Unix-specific modules.

## Features

- 🔍 Network scanning with CIDR notation support
- 🔑 Multiple credential testing
- 🛣️ Common RTSP path discovery
- 🧵 Multi-threaded for faster scanning
- 📊 Progress reporting
- 💾 Optional JSON output

## Requirements

- Python 3.6 or higher
- FFmpeg installed and available in your PATH

## Installation

1. **Install Python** (if not already installed)
   - Download from [python.org](https://www.python.org/downloads/windows/)
   - During installation, make sure to check "Add Python to PATH"

2. **Install FFmpeg**
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Extract the files to a folder (e.g., `C:\ffmpeg`)
   - Add the `bin` folder to your PATH:
     - Open Control Panel → System → Advanced System Settings → Environment Variables
     - Edit the PATH variable and add the path to FFmpeg's bin folder (e.g., `C:\ffmpeg\bin`)
     - Verify the installation by opening a new Command Prompt and typing:
       ```
       ffmpeg -version
       ```

3. **Download the scanner script**
   - Save the `windows_rtsp_scanner.py` file to your computer

## Usage

### Basic Command

```
python windows_rtsp_scanner.py -a 192.168.1.0/24
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-a`, `--address` | IP address or network in CIDR notation | `192.168.1.0/24` |
| `-p`, `--ports` | Comma-separated list of ports to scan | `554,8554` |
| `-c`, `--credentials` | Comma-separated list of credentials in format username:password | None |
| `-P`, `--paths` | Comma-separated list of RTSP paths to try | Various common paths |
| `-t`, `--timeout` | Timeout in seconds for each RTSP test | `10` |
| `-r`, `--retries` | Number of retries for each RTSP test | `2` |
| `-o`, `--output` | Output file for discovered cameras (JSON format) | None |
| `-w`, `--workers` | Maximum number of concurrent workers | `50` |

### Examples

#### Scan your local network with default settings
```
python windows_rtsp_scanner.py -a 192.168.1.0/24
```

#### Scan with specific credentials
```
python windows_rtsp_scanner.py -a 192.168.1.0/24 -c admin:admin
```

#### Try multiple credential sets
```
python windows_rtsp_scanner.py -a 192.168.1.0/24 -c admin:admin,admin:password,root:root
```

#### Scan specific ports
```
python windows_rtsp_scanner.py -a 192.168.1.0/24 -p 554,8554,10554
```

#### Custom RTSP paths
```
python windows_rtsp_scanner.py -a 192.168.1.0/24 -P /live,/h264Preview_01_main,/Streaming/Channels/101
```

#### Save results to a file
```
python windows_rtsp_scanner.py -a 192.168.1.0/24 -o results.json
```

#### Scan a specific IP address
```
python windows_rtsp_scanner.py -a 192.168.1.100/32
```

#### Reduce timeout for faster scanning (but potentially missing slow streams)
```
python windows_rtsp_scanner.py -a 192.168.1.0/24 -t 5
```

## Understanding the Output

The scanner outputs information in several stages:

1. **Port Scanning Phase**:
   - Shows progress as it scans your network
   - Reports open ports as they're found

2. **RTSP Testing Phase**:
   - Tests each open port with various RTSP paths
   - Reports successful connections

3. **Results Summary**:
   - Lists all discovered potential RTSP sources (open ports)
   - Lists all working RTSP streams with their URLs

## Common RTSP Paths

The scanner tests the following common RTSP paths by default:
- `/Streaming/Channels/101` (Hikvision)
- `/live` (Generic)
- `/live2` (Generic alternative)
- `/h264Preview_01_main` (Some IP cameras)
- `/h264Preview_01_sub` (Sub-stream for some IP cameras)
- `/cam/realmonitor` (Dahua)
- `/live/ch00_0` (Various IP cameras)
- `/live/ch00_1` (Various IP cameras)

You can specify custom paths using the `-P` option.

## Common Credentials

Most IP cameras use one of these default credentials:
- admin:admin
- admin:password
- admin:12345
- admin:[blank]
- root:root
- root:admin
- root:password

**Important**: Always change default passwords on your cameras after installation!

## Troubleshooting

### FFmpeg Not Found
If you see "Error: ffmpeg is required but not found in PATH":
1. Make sure FFmpeg is installed
2. Verify FFmpeg is in your PATH by typing `ffmpeg -version` in a command prompt
3. If the command doesn't work, revisit the FFmpeg installation steps

### No Open Ports Found
1. Verify your network address is correct
2. Try scanning different ports (`-p` option)
3. Check your firewall settings

### No Working Streams Found
1. Try different credentials (`-c` option)
2. Try different RTSP paths (`-P` option)
3. Increase timeout (`-t` option) and retries (`-r` option)

## Security Note

This tool is intended for network administrators to discover cameras on networks they own or have permission to scan. Using it on networks without permission may violate laws and regulations.

## License

This software is provided "as is", without warranty of any kind.

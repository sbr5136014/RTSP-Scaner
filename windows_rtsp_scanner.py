#!/usr/bin/env python
# Windows-compatible RTSP Scanner
# No dependency on the Unix-specific 'resource' module

import os
import subprocess
import argparse
import ipaddress
import socket
import concurrent.futures
import time
import json
from urllib.parse import quote_plus

# Check if ffmpeg is available
def check_ffmpeg():
    try:
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return True
    except FileNotFoundError:
        return False

# Port scanner for Windows that doesn't rely on the resource module
def scan_port(ip, port, timeout=1):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except socket.error:
        return False

# Scan a range of IPs and ports
def scan_network(address, ports, max_workers=50):
    open_ports = []
    
    # Parse CIDR notation or single IP
    try:
        network = ipaddress.ip_network(address, strict=False)
    except ValueError:
        print(f"Invalid IP address or network: {address}")
        return []
    
    # Convert ports string to list of integers
    port_list = [int(port.strip()) for port in ports.split(',')]
    
    # Calculate total scans for progress reporting
    total_ips = len(list(network.hosts()))
    total_scans = total_ips * len(port_list)
    completed = 0
    
    print(f"Scanning {total_ips} IP addresses across {len(port_list)} ports...")
    print(f"Total scans to perform: {total_scans}")
    
    # Use ThreadPoolExecutor for concurrent scanning
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        
        # Submit all scan tasks
        for ip in network.hosts():
            ip_str = str(ip)
            for port in port_list:
                futures.append(executor.submit(scan_port, ip_str, port))
                
        # Process results as they complete
        for i, (ip, port, future) in enumerate(zip(
            [str(ip) for ip in network.hosts() for _ in port_list],
            [port for _ in range(total_ips) for port in port_list],
            concurrent.futures.as_completed(futures)
        )):
            completed += 1
            
            # Update progress every 100 scans
            if completed % 100 == 0 or completed == total_scans:
                progress = (completed / total_scans) * 100
                print(f"Progress: {completed}/{total_scans} ({progress:.1f}%)", end='\r')
            
            if future.result():
                result = {"ip": ip, "port": port, "open": True}
                open_ports.append(result)
                print(f"\nFound open port: {ip}:{port}                ")
    
    print(f"\nCompleted {total_scans} scans. Found {len(open_ports)} open ports.")
    return open_ports

# Test RTSP stream with ffmpeg
def test_rtsp_stream(ip, port, path, credentials=None, timeout=10, retries=2):
    if credentials and credentials.lower() != "none":
        transport = f"rtsp://{credentials}@"
    else:
        transport = "rtsp://"
    
    # Ensure path starts with a slash
    if not path.startswith('/'):
        path = '/' + path
        
    rtsp_url = f"{transport}{ip}:{port}{path}"
    snapshot = os.path.join(os.environ.get('TEMP', '.'), f"rtsp_test_{ip}_{port}_{path.replace('/', '_')}.png")
    
    # Build ffmpeg command
    command = [
        'ffmpeg', 
        '-y',                    # Overwrite output file
        '-loglevel', 'error',    # Minimal logging
        '-rtsp_transport', 'tcp',
        '-i', rtsp_url,
        '-frames:v', '1',        # Capture only one frame
        snapshot
    ]
    
    print(f"Testing: {rtsp_url}")
    
    # Try multiple times in case of timeout
    for attempt in range(retries):
        try:
            result = subprocess.run(
                command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                timeout=timeout,
                check=False
            )
            
            # Check if the snapshot file was created and has content
            if result.returncode == 0 and os.path.exists(snapshot) and os.path.getsize(snapshot) > 0:
                print(f"✅ Success: {rtsp_url}")
                return True, rtsp_url
            else:
                # Clean up error output for display
                error = result.stderr.decode('utf-8', errors='replace').strip()
                if error:
                    print(f"❌ Error: {error}")
                
            # Delete failed snapshot
            if os.path.exists(snapshot):
                os.remove(snapshot)
                
        except subprocess.TimeoutExpired:
            print(f"⏱️ Timeout on attempt {attempt+1}/{retries}")
            
    return False, rtsp_url

def main():
    parser = argparse.ArgumentParser(description="Scan for RTSP cameras on your network")
    parser.add_argument('-a', '--address', type=str, required=False, default='192.168.1.0/24',
                        help="IP address or network in CIDR notation (e.g., 192.168.1.0/24)")
    parser.add_argument('-p', '--ports', type=str, required=False, default='554,8554',
                        help="Comma-separated list of ports to scan (e.g., 554,8554)")
    parser.add_argument('-c', '--credentials', type=str, required=False, default=None,
                        help="Credentials in format username:password (e.g., admin:admin)")
    parser.add_argument('-P', '--paths', type=str, required=False, 
                        default='/onvif/profile1/media.smp,/,/1,/Streaming/Channels/1,/profile5/media.smp,/onvif/profile5/media.smp,/onvif/profile2/media.smp,/profile2/media.smp,/cam/h264,/live/ch00_0,/live/h264/ch1,/cam/realmonitor?channel=1&subtype=1,/cam/realmonitor?channel=1&subtype=00,/0/main,/mpeg4unicast,/MediaInput/h264,/profile1/media.smp,/mpeg4/1/media.amp,/h264_pcm.sdp,/onvif/profile4/media.smp,/profile4/media.smp,/onvif/profile6/media.smp,/mjpeg/media.smp,/MJPEG/media.smp,/H264/media.smp,/profile1/media.smp,/Streaming/Channels/101,/live,/live2,/h264Preview_01_main,/h264Preview_01_sub,/cam/realmonitor',
                        help="Comma-separated list of RTSP paths to try")
    parser.add_argument('-t', '--timeout', type=int, required=False, default=10,
                        help="Timeout in seconds for each RTSP test")
    parser.add_argument('-r', '--retries', type=int, required=False, default=2,
                        help="Number of retries for each RTSP test")
    parser.add_argument('-o', '--output', type=str, required=False, default=None,
                        help="Output file for discovered cameras (JSON format)")
    parser.add_argument('-w', '--workers', type=int, required=False, default=50,
                        help="Maximum number of concurrent workers")
    
    args = parser.parse_args()
    
    # Check for ffmpeg
    if not check_ffmpeg():
        print("Error: ffmpeg is required but not found in PATH")
        print("Please install ffmpeg and make sure it's in your PATH")
        return
    
    # Split paths
    paths = [p.strip() for p in args.paths.split(',')]
    
    # Split credentials
    credentials_list = []
    if args.credentials:
        credentials_list = [c.strip() for c in args.credentials.split(',')]
    
    # Add empty credentials for testing without auth
    if None not in credentials_list:
        credentials_list.append(None)
    
    # Scan network for open ports
    print(f"Starting network scan for {args.address}")
    open_ports = scan_network(args.address, args.ports, args.workers)
    
    if not open_ports:
        print("No open ports found. Try scanning different ports or address range.")
        return
    
    # Test RTSP streams on open ports
    print("\nTesting RTSP streams on open ports...")
    successful_streams = []
    flaky_streams = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = []
        
        for result in open_ports:
            ip = result["ip"]
            port = result["port"]
            
            for path in paths:
                for creds in credentials_list:
                    futures.append(
                        executor.submit(
                            test_rtsp_stream, 
                            ip, 
                            port, 
                            path, 
                            creds, 
                            args.timeout, 
                            args.retries
                        )
                    )
        
        for future in concurrent.futures.as_completed(futures):
            success, rtsp_url = future.result()
            if success:
                successful_streams.append(rtsp_url)
    
    # Print results
    print("\n===== SCAN RESULTS =====")
    print(f"Discovered {len(open_ports)} potential RTSP sources:")
    for result in open_ports:
        print(f"  {result['ip']}:{result['port']}")
    
    print(f"\nDiscovered {len(successful_streams)} working RTSP streams:")
    for stream in successful_streams:
        print(f"  {stream}")
    
    # Save results to file if requested
    if args.output:
        results = {
            "scan_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "address_range": args.address,
            "ports_scanned": args.ports,
            "open_ports": open_ports,
            "working_streams": successful_streams
        }
        
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nScan interrupted by user.")
    except Exception as e:
        print(f"Error: {e}")

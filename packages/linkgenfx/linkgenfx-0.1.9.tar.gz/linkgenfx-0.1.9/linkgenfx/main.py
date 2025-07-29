import subprocess
import time
import os
import signal
import sys
import socket
import platform
import tempfile

def clear_line():
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()

def print_aligned(message):
    clear_line()
    print(message)

def set_terminal_title():
    if platform.system() == "Windows":
        os.system("title LinkGen V4")
    else:
        sys.stdout.write("\x1b]2;LinkGen V4\x07")
        sys.stdout.flush()

def show_help():
    print("""
Usage:
  python app.py                   # Default TCP mode on port 3389
  python app.py 5555              # TCP on port 5555
  python app.py tcp 4444          # Explicit TCP on port 4444
  python app.py http 8080         # HTTP mode on port 8080
  python app.py -h / --help       # Show this help
    """)
    sys.exit(0)

# Parse args
MODE = "tcp"
PORT = 3389
args = sys.argv[1:]

if "-h" in args or "--help" in args:
    show_help()

if len(args) == 1 and args[0].isdigit():
    PORT = int(args[0])
elif len(args) == 2:
    if args[0] in ["tcp", "http"] and args[1].isdigit():
        MODE = args[0]
        PORT = int(args[1])
    else:
        show_help()
elif len(args) > 2:
    show_help()

# Constants
LOG_FILE = os.path.join(tempfile.gettempdir(), "serveo_output.log")
SERVEO_DOMAIN = "serveo.net"
TIMEOUT = 60
process = None

def cleanup(signum=None, frame=None):
    global process
    if process:
        print_aligned("\n[+] Cleaning up SSH tunnel process...")
        try:
            if platform.system() == "Windows":
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(process.pid)])
            else:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except Exception as e:
            print_aligned(f"[!] Exception during cleanup: {e}")
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def main():
    global process
    set_terminal_title()

    print_aligned(f"[+] Starting SSH reverse tunnel ({MODE.upper()}) to {SERVEO_DOMAIN} on port {PORT}")
    print_aligned("[>] Please wait while establishing tunnel...")

    with open(LOG_FILE, "w") as log_file:
        if MODE == "http":
            ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-R", f"80:localhost:{PORT}", SERVEO_DOMAIN]
        else:
            ssh_cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-R", f"0:localhost:{PORT}", SERVEO_DOMAIN]

        if platform.system() == "Windows":
            process = subprocess.Popen(ssh_cmd, stdout=log_file, stderr=subprocess.STDOUT,
                                       creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            process = subprocess.Popen(ssh_cmd, stdout=log_file, stderr=subprocess.STDOUT,
                                       preexec_fn=os.setsid)

    # Wait for Serveo response
    start_time = time.time()
    success = False
    link_line = None
    log_content = ""

    while time.time() - start_time < TIMEOUT:
        try:
            with open(LOG_FILE, "r") as f:
                log_content = f.read()
                if "Forwarding" in log_content:
                    success = True
                    break
        except FileNotFoundError:
            pass
        time.sleep(1)

    if not success:
        print_aligned(f"\n[✗] Error: Failed to establish tunnel within {TIMEOUT} seconds")
        print_aligned(f"[!] Check log: {LOG_FILE}")
        cleanup()

    try:
        serveo_ip = socket.gethostbyname(SERVEO_DOMAIN)
    except socket.gaierror:
        print_aligned(f"\n[✗] Error: Unable to resolve {SERVEO_DOMAIN}")
        cleanup()

    # Parse output
    http_link = None
    rport = None

    for line in log_content.splitlines():
        if MODE == "http" and "Forwarding HTTP traffic from" in line:
            http_link = line.split("from")[-1].strip()
        if MODE == "tcp" and "Forwarding TCP" in line and ":" in line:
            rport = line.split(":")[-1].strip()

    print_aligned("")
    print_aligned("[>] Linkgen V5 By EFXTv")
    print_aligned(f"[>] IP     : {serveo_ip}")
    print_aligned(f"[>] MODE   : {MODE.upper()}")

    if MODE == "http":
        print_aligned(f"[>] LINK   : {http_link if http_link else 'Unavailable'}")
    else:
        print_aligned(f"[>] RPORT  : {rport if rport else 'Unknown'}")

    print_aligned(f"[>] LPORT  : {PORT}")
    print_aligned("")
    print_aligned("[>] Press Ctrl+C to exit and cleanup.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()

if __name__ == "__main__":
    main()

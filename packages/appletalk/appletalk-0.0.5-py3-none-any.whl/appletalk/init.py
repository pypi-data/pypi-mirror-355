import subprocess
import sys
sys.dont_write_bytecode = True

def run_applescript(script):
    process = subprocess.Popen(
        ["osascript", "-"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    out, err = process.communicate(script.encode())
    if err and b"error" in err:
        raise Exception(f"AppleScript error: {err.decode().strip()}")
    return out.decode()


# Example: Get the name of the frontmost app
if __name__ == "__main__":
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    front_app = run_applescript(script)
    print(f"Frontmost app is: {front_app}")

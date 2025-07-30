try:
    from . import init
except:
    import init


def get_focused_app():
        script = 'tell application "System Events" to get name of first application process whose frontmost is true'
        return init.run_applescript(script)
def get_focused_windows():
    script = '''
    tell application "System Events"
        set frontApp to first application process whose frontmost is true
        get name of every window of frontApp
    end tell
    '''
    try:
        result = init.run_applescript(script)
    except Exception as e:
        result = False
        print(f"you should probably give this process permission control your computer. Exact error: {e}")
    # AppleScript returns a comma-separated string for multiple windows
    # If no windows, it may return an empty string or error; handle that
    if result:
        return [w.strip() for w in result.split(",")]
    else:
        return []

def get_app_windows_info(app_name: str) -> dict:
    script = f'''
    tell application "System Events"
        set appProc to first application process whose name is "{app_name}"
        set windowNames to name of every window of appProc
        return (count of windowNames) & "::" & (windowNames as string)
    end tell
    '''
    try:
        result = init.run_applescript(script)
    except Exception as e:
        result = False
        print(f"you should probably give this process permission control your computer. Exact error: {e}")
        return {"count": 0, "windows": []}
    if "::" in result:
        count_str, names_str = result.split("::", 1)
        count = int(count_str)
        names = [n.strip() for n in names_str.split(",")] if names_str else []
        return {"count": count, "windows": names}
    return {"count": 0, "windows": []}

def list_all_visible_windows() -> list[str]:
    script = '''
    tell application "System Events"
        set allWindows to {}
        repeat with proc in application processes
            repeat with w in windows of proc
                set end of allWindows to name of w
            end repeat
        end repeat
        return allWindows
    end tell
    '''
    windows = init.run_applescript(script)
    if windows:
        return [w.strip() for w in windows.split(",")]
    return []

def get_desktop_wallpaper() -> str:
    script = '''
    tell application "System Events"
        get picture of current desktop
    end tell
    '''
    return init.run_applescript(script)

def get_all_apps():
    script = 'tell application "System Events" to get name of every application process'
    return init.run_applescript(script).split(', ')

def focus_app(app_name: str) -> None:
    script = f'tell application "{app_name}" to activate'
    init.run_applescript(script)

def quit_app(app_name: str) -> None:
    script = f'''
    tell application "System Events"
        if (name of every process) contains "{app_name}" then
            tell application "{app_name}" to quit
        end if
    end tell
    '''
    init.run_applescript(script)

def is_app_running(app_name: str) -> bool:
    script = f'''
    tell application "System Events"
        return (name of every process) contains "{app_name}"
    end tell
    '''
    result = init.run_applescript(script)
    return result.lower() == 'true'
# screenshot.py
import subprocess
import datetime
import os

def take_screenshot(save_to: str = None, issilent=True) -> str:
    if not save_to:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        save_to = os.path.expanduser(f"~/Desktop/screenshot-{timestamp}.png")

    try:
        subprocess.run(["screencapture", "-x" if issilent else "", save_to], check=True)
        return save_to
    except subprocess.CalledProcessError as e:
        raise Exception(f"Failed to take screenshot: {e}")

# Optional: Take and print path
def relaunch_app(app):
    script=f'''
    tell application "{app}"
    quit
    delay 2
    launch
    activate
    end tell
    '''
    init.run_applescript(script)
def launch_app(app_name: str) -> None:
    script = f'tell application "{app_name}" to launch'
    init.run_applescript(script)
def change_desktop_wallpaper(image_path: str) -> None:
    script = f'''
    tell application "System Events"
        set picture of current desktop to POSIX file "{image_path}"
    end tell
    '''
    init.run_applescript(script)
def change_shot_type(ex):
    script =f'do shell script "defaults write com.apple.screencapture type {ex}; killall SystemUIServer"'
    init.run_applescript(script)
def restart_computer():
    init.run_applescript('tell application "System Events" to restart')
def shutdown_computer():
    init.run_applescript('tell application "System Events" to shut down')
def sleep_computer():
    init.run_applescript('tell application "System Events" to sleep')
def log_out_user():
    init.run_applescript('tell application "System Events" to log out')
def cpu_overload(inputt=True):
    # Start a background 'yes' process to overload the CPU
    proc = subprocess.Popen(['yes'], stdout=subprocess.DEVNULL)

    try:
        if inputt:
            input("Press Enter to stop the CPU overload...")
    finally:
        # Stop the process cleanly
        proc.terminate()
        proc.wait()




if __name__ == "__main__":
    import time
    #relaunch_app("Finder")
    #launch_app("Safari")
    #change_shot_type("png")
    #wal = get_desktop_wallpaper()
    #print(wal)
    #change_desktop_wallpaper(os.path.expanduser("~/Desktop/IMG_0140.jpeg"))
    #time.sleep(5)
    #change_desktop_wallpaper(wal)
    cpu_overload()
try:
    from . import init
except:
    import init

def start_screen_recording() -> None:
    script = '''
    tell application "QuickTime Player"
        activate
        start (new screen recording)
    end tell
    '''
    init.run_applescript(script)

def play_pause() -> None:
    script = '''
    tell application "QuickTime Player"
        if not (exists front document) then return
        tell front document
            if playing then
                pause
            else
                play
            end if
        end tell
    end tell
    '''
    init.run_applescript(script)
def stop() -> None:
    script = '''
    tell application "QuickTime Player"
        if exists front document then
            tell front document to stop
        end if
    end tell
    '''
    init.run_applescript(script)

def get_status() -> str:
    script = '''
    tell application "QuickTime Player"
        if exists front document then
            set isPlaying to playing of front document
            if isPlaying then
                return "playing"
            else
                return "paused"
            end if
        else
            return "no document"
        end if
    end tell
    '''
import subprocess
def stop_screen_recording():
    subprocess.run(["osascript", "-e", 'tell application "QuickTime Player" to stop (every recording)'], stderr=subprocess.DEVNULL)
if __name__ == "__main__":
    import time
    start_screen_recording()
    time.sleep(1)
    stop_screen_recording()
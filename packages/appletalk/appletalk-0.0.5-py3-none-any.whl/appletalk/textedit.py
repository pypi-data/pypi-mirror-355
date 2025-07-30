try:
    from . import init
except:
    import init

def write(text="Hello from AppleScript!"):
    script = f'''
    tell application "TextEdit"
        activate
        make new document
        set the text of the front document to "{text}"
    end tell
    '''
    return init.run_applescript(script)
import subprocess
def open_text(filepath):
    script = f'''
    tell application "TextEdit"
        open POSIX file "{filepath}"
        activate
    end tell
    '''
    subprocess.run(['osascript', '-e', script])
if __name__ == "__main__":
    import os
    open_text(os.path.expanduser("/Applications/Utilities/Adobe Creative Cloud/Components/CCLibs/resources/designLibraries/327.bundle.js"))
    write()
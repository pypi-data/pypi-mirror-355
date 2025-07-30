
try:
    from . import init
except:
    import init
def get_finder_front_window_path() -> str:
    script = '''
    tell application "Finder"
        try
            set thePath to (POSIX path of (target of front window as alias))
            return thePath
        on error
            return ""
        end try
    end tell
    '''
    return init.run_applescript(script)
def empty_trash() -> None:
    script = '''
    tell application "Finder"
        empty the trash
    end tell
    '''
    init.run_applescript(script)

def move_to_trash(path: str) -> None:
    script = f'''
    tell application "Finder"
        delete POSIX file "{path}"
    end tell
    '''
    init.run_applescript(script)
def get_finder_selection() -> list[str]:
    script = '''
    tell application "Finder"
        set selectedItems to selection
        set itemPaths to {}
        repeat with i in selectedItems
            set end of itemPaths to POSIX path of (i as alias)
        end repeat
        return itemPaths as string
    end tell
    '''
    result = init.run_applescript(script)
    return [item.strip() for item in result.split(",")] if result else []
def reveal_in_finder(path: str) -> None:
    script = f'''
    tell application "Finder"
        reveal POSIX file "{path}"
        activate
    end tell
    '''
    init.run_applescript(script)
def open_folder_in_finder(path: str) -> None:
    script = f'''
    tell application "Finder"
        open POSIX file "{path}"
        activate
    end tell
    '''
    init.run_applescript(script)
import subprocess

def quick_look_file(filepath):
    subprocess.run(["qlmanage", "-p", filepath])




if __name__ == "__main__":
    import os
    print(get_finder_front_window_path())
    #open_folder_in_finder(os.path.expanduser("~"))
    quick_look_file(os.path.expanduser("~/Documents/TESTTEST/TESTTEST/TESTTESTApp.swift"))
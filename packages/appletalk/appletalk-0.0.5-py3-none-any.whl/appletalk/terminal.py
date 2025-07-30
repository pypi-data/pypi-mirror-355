try:
    from . import init
except:
    import init

def run_command(command: str, visible: bool = True):
    if visible:
        script = f'''
        tell application "Terminal"
            activate
            do script "{command}"
        end tell
        '''
    else:
        # run hidden via `do shell script`
        script = f'''set homeContents to do shell script "{command}"
                    display dialog homeContents'''
    
    init.run_applescript(script)
def capture_command_output(command: str) -> str:
    script = f'''set homeContents to do shell script "{command}"
                    return homeContents'''
    
    return init.run_applescript(script)
if __name__ == "__main__":
    run_command("echo 'Hello, World!'", visible=True)
    run_command("echo 'This is hidden'", visible=False)
    run_command("ls -l", visible=True)
    run_command("pwd", visible=False)
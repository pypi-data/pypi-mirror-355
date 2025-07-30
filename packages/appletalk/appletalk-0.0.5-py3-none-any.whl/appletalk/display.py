try:
    from . import init
except:
    import init

def display_dialog(message, title="Alert", buttons=("OK","lo"), default_button="OK"):
    btns = '", "'.join(buttons)
    script = f'''
    display dialog "{message}" with title "{title}" buttons {{"{btns}"}} default button "{default_button}"
    '''
    return init.run_applescript(script)
def display_notification(text, title="Notification", subtitle=""):
    "notification popup for macos"
    script = f'display notification "{text}" with title "{title}" subtitle "{subtitle}"'
    return init.run_applescript(script)
def display_text_input(prompt, default_answer="", title="Input"):
    "macos style text input dialog"
    script = f'''
try
    set userResponse to display dialog "{prompt}" default answer "{default_answer}" with title "{title}"
    set buttonPressed to button returned of userResponse
    set textEntered to text returned of userResponse
    return buttonPressed & "||" & textEntered
on error number -128
    return "Cancel||"
end try


    '''
    output = init.run_applescript(script)
    button, text = output.split("||", 1)
    return [button.strip(), text.strip()]
def display_alert(text, as_critical=False, giving_up_after=None):
    "displays a macos alert"
    critical = "as critical" if as_critical else ""
    timeout = f'giving up after {giving_up_after}' if giving_up_after else ""
    script = f'display alert "{text}" {critical} {timeout}'
    return init.run_applescript(script)
if __name__ == "__main__":
    # Example usage
    print(display_dialog("This is a test message", "Test Title", ("OK", "Cancel"), "OK"))
    display_alert("DA WORLD GONNA END", as_critical=True, giving_up_after=5)
    display_notification("This is a test notification", "Test Notification", "Subtitle")
    print(display_text_input("Please enter your name:", "Default Name", "Input Title"))
try:
    from . import init
except:
    import init
PANEL_IDS = {
    "general": "com.apple.preference.general",
    "desktop_and_screen_saver": "com.apple.preference.desktopscreeneffect",
    "dock": "com.apple.preference.dock",
    "mission_control": "com.apple.preference.expose",
    "language_and_region": "com.apple.preference.language",
    "security_and_privacy": "com.apple.preference.security",
    "network": "com.apple.preference.network",
    "bluetooth": "com.apple.preference.bluetooth",
    "sound": "com.apple.preference.sound",
    "notifications": "com.apple.preference.notifications",
    "accessibility": "com.apple.preference.universalaccess",
}
def open_panel(panel):
    """
    Open a specific System Settings panel by its identifier.
    
    :param panel: The identifier of the System Settings panel to open.
    """
    script = f'''
    tell application "System Settings"
        reveal pane id "{panel}"
        activate
    end tell
    '''
    init.run_applescript(script)
if __name__ == "__main__":
    open_panel(PANEL_IDS['sound'])
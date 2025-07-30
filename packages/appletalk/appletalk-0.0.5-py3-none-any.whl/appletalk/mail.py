try:
    from . import init
except:
    import init
import subprocess
def get_unread_email_subjects() -> list[str]:
    script = '''
    tell application "Mail"
        set unreadMessages to messages of inbox whose read status is false
        set subjects to {}
        repeat with msg in unreadMessages
            set end of subjects to subject of msg
        end repeat
        return subjects as string
    end tell
    '''
    result = init.run_applescript(script)
    return result.split(", ")
def get_unread_email_senders():
    script = '''
    tell application "Mail"
        set unreadMessages to messages of inbox whose read status is false
        set senderList to {}
        repeat with msg in unreadMessages
            set end of senderList to sender of msg
        end repeat
        return senderList
    end tell
    '''
    result = init.run_applescript(script)
    if result.strip():
        return [s.strip() for s in result.split(", ")]
    return []
def count_unread_emails():
    script = '''
    tell application "Mail"
        set unreadCount to count (messages of inbox whose read status is false)
        return unreadCount
    end tell
    '''
    result = init.run_applescript(script)
    return int(result.strip()) if result.strip().isdigit() else 0
def mark_all_as_read():
    script = '''
    tell application "Mail"
        set unreadMessages to messages of inbox whose read status is false
        repeat with msg in unreadMessages
            set read status of msg to true
        end repeat
    end tell
    '''
    init.run_applescript(script)
def delete_emails_by_subject(subject_text):
    # Deletes all emails in Inbox with matching subject (case sensitive)
    script = f'''
    tell application "Mail"
        set targetMessages to messages of inbox whose subject is "{subject_text}"
        repeat with msg in targetMessages
            delete msg
        end repeat
    end tell
    '''
    init.run_applescript(script)
def reply_to_latest_unread_email(template="Thanks for your email!"):
    script = f'''
    tell application "Mail"
        set unreadMessages to messages of inbox whose read status is false
        if unreadMessages is not {{}} then
            set latestMsg to item 1 of unreadMessages
            set replyMsg to reply latestMsg with opening window
            tell replyMsg
                set content to "{template}" & return & content
                send
            end tell
        end if
    end tell
    '''
    init.run_applescript(script)
def send_email(recipient, subject, body, visible="true"):
    script = f'''
    tell application "Mail"
        set newMessage to make new outgoing message with properties {{subject:"{subject}", content:"{body}", visible:{visible}}}
        tell newMessage
            make new to recipient at end of to recipients with properties {{address:"{recipient}"}}
            send
        end tell
    end tell
    '''
    init.run_applescript(script)

def send_email_with_attachment(to, subject, content, attachment_path=None, visible="true", html=False):
    # Determine visibility
    visibility_clause = "activate" if visible.lower() == "true" else ""

    # Escape double quotes and backslashes in the HTML content
    safe_content = content.replace("\\", "\\\\").replace('"', '\\"')

    # Use HTML or plain text
    content_type = 'html' if html else 'plain text'

    # Build AppleScript
    script = f'''
    tell application "Mail"
        {visibility_clause}
        set newMessage to make new outgoing message with properties {{subject:"{subject}", visible:true}}
        tell newMessage
            make new to recipient at end of to recipients with properties {{address:"{to}"}}
            set content to "{safe_content}"
            set message type to {content_type}
    '''

    if attachment_path:
        safe_path = attachment_path.replace("\\", "\\\\").replace('"', '\\"')
        script += f'''
            try
                make new attachment with properties {{file name:"{safe_path}"}} at after the last paragraph
            end try
        '''

    script += '''
            send
        end tell
    end tell
    '''

    init.run_applescript(script)

def send_eml_via_mail(eml_path, visible=True):
    script = f'''
    tell application "Mail"
        set theMessage to open POSIX file "{eml_path}"
        {'activate' if visible else ''}
        send theMessage
    end tell
    '''
    subprocess.run(['osascript', '-e', script], check=True)





if __name__ == "__main__":
    #import os
    #send_email(
    #    subject="test", 
    #    recipient="", 
    #    body="This is a test email from Appletalk.", 
    #    visible="false"
    #)
    pass
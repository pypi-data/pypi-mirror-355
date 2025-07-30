try:
    from . import init
except:
    import init
def add_contact(firstname, lastname, email, label="work"):
    script = f'''
tell application "Contacts"
    set thePerson to make new person with properties {{first name:"{firstname}", last name:"{lastname}"}}
    make new email at end of emails of thePerson with properties {{label:"{label}", value:"{email}"}}
    save
end tell
'''
    init.run_applescript(script)
def get_contacts():
    script = '''
tell application "Contacts"
    set nameList to {}
    repeat with aPerson in every person
        set end of nameList to name of aPerson
    end repeat
    return nameList
end tell
    '''
    return init.run_applescript(script)
def deletebyname(name):
    script = f'''
tell application "Contacts"
    set matches to every person whose name is "{name}"
    if matches is not {{}} then
        delete item 1 of matches
        return "Deleted John Doe"
    else
        return "No contact named {name} found"
    end if
end tell
    '''
    return init.run_applescript(script)

if __name__ == "__main__":
    import time
    add_contact("John", "Doe", "rana.yavuz@thekaustschool.org")
    time.sleep(1)
    print(deletebyname("John Doe"))
    print(get_contacts())
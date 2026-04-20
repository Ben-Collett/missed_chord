import subprocess
import os
def sudo_safe_send_notification(title:str, message:str, duration_ms:int):
    """
    sends a notification using notify-send safe even when ran as root
    if being ran as root user from a user account using something like sudo sudo is a hard dependency.
    """
    original_user = _get_original_user()
    user_id = None
    # WARNING: cmd must be handled with care to prevent shell injection
    # when using a list this is taken care of for us when using a string
    # we need to guard against a bad actor escaping the title/content/duration using a " and injection a malicouse command
    cmd = ["notify-send", "-t", str(duration_ms), title, message]

    if original_user:
        user_id = _get_user_id(original_user)

    if user_id:
        dbus_path = f"/run/user/{user_id}/bus"
        if os.path.exists(dbus_path):
            cmd = ["sudo", "-u", original_user, "DISPLAY=:0", f"DBUS_SESSION_BUS_ADDRESS=unix:path={dbus_path}", "notify-send", "-t", str(duration_ms), title, message]
        else:

            cmd = ["sudo", "-u", original_user, "DISPLAY=:0", "notify-send", "-t", str(duration_ms), title, message]

    subprocess.run(cmd, check=True)

def _get_original_user()->str|None:
    """
    use SUDO_USER environment variable to get the name of the original user
    this should be set by the sudo command but if it isn't the logname command is used as a fallback
    """
    return os.environ.get("SUDO_USER") or _get_logname()

def _get_logname():
    """
    returns the users log in name
    instead of the current user so in my case it will
    always return ben instead of root or something similar
    returns none if the logname command failed
    """
    try:
        return subprocess.run(
            ["logname"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        return None


def _get_user_id(username):
    """
    uses id command to get a users id from there username
    id should be installed on most machines since it's a GNU core util
    """
    try:
        return str(
            subprocess.run(
                ["id", "-u", username],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )
    except subprocess.CalledProcessError:
        return None



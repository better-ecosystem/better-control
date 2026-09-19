import subprocess
from better_control.utils.logger import Logger, LogLevel

def notify_send(
    logging:Logger,
    app_name="",
    urgency="normal",
    app_icon="settings",
    icon="",
    summary="",
    body="",
    actions_array=None
):
    """ Send notification using notify-send
    
    args:
        app_name: Applicarion name
        urgency: Specifies the notification urgency level (low, normal, critical).
            default: normal
        app_icon: Application icon
        icon: Custom path/to/icon to display
        summary: Summary of notification
        body: Body of notification
        actions: list of actions to display in notification with {id, label}
    
    """
    actions_array = actions_array or []

    command = [
        "notify-send",
        "-u", urgency,
        "-i", app_icon,
        summary,
        body,
        "-a", app_name,
        *[f'--action={v["id"]}={v["label"]}' for v in actions_array]
    ]

    command = [arg for arg in command if arg]

    try:
        subprocess.run(command, check=True)
    except subprocess.SubprocessError as err:
        logging.log(LogLevel.Error, f"Error sending notification: {err}")

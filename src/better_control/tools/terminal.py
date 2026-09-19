import subprocess


def term_support_color() -> bool:
    result = subprocess.run(["tput", "colors"], capture_output=True, text=True).stdout
    return result.strip() == "256"

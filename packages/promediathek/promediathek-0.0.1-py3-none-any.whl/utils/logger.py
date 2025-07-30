console_log = False


def enable_console_log():
    global console_log
    console_log = True


def log(level, msg):
    open(f'{level.lower()}.log', 'a', encoding='utf-8').write(f"[{level}] {msg}\n")

    if console_log:
        print(f"[{level}] {msg}")

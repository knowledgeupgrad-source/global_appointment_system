OFFSET_FILE = ".telegram_offset"


def get_last_offset() -> int:
    try:
        with open(OFFSET_FILE, "r") as f:
            return int(f.read())
    except:
        return 0


def save_last_offset(offset: int):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))

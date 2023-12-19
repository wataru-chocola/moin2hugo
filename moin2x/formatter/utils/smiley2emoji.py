__all__ = ["smiley2emoji"]

smiley2emoji_map = {
    "X-(": ":angry:",
    ":D": ":smiley:",
    "<:(": ":frowning:",
    ":o": ":astonished:",
    ":(": ":frowning:",
    ":)": ":simple_smile:",
    "B)": ":sunglasses:",
    ":))": ":simple_smile:",
    ";)": ":wink:",
    "/!\\": ":exclamation:",
    "<!>": ":exclamation:",
    "(!)": ":bulb:",
    ":-?": ":stuck_out_tongue_closed_eyes:",
    ":\\": ":astonished:",
    ">:>": ":angry:",
    "|)": ":innocent:",
    ":-(": ":frowning:",
    ":-)": ":simple_smile:",
    "B-)": ":sunglasses:",
    ":-))": ":simple_smile:",
    ";-)": ":wink:",
    "|-)": ":innocent:",
    "(./)": ":white_check_mark:",
    "{OK}": ":thumbsup:",
    "{X}": ":negative_squared_cross_mark:",
    "{i}": ":information_source:",
    "{1}": ":one:",
    "{2}": ":two:",
    "{3}": ":three:",
    "{*}": ":star:",
    "{o}": ":star2:",
}


def smiley2emoji(smiley: str) -> str:
    return smiley2emoji_map[smiley]

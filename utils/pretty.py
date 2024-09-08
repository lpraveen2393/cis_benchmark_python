def pretty_underline(text:str, underline: str ="="):
    try:
        print(len(text.splitlines()[-1]) * underline)
    except:
        print()

def pretty_print(text: str, underline: str = "=", upper_underline: bool = False):
    if upper_underline:
        pretty_underline(text, underline)
    print(text)
    pretty_underline(text, underline)
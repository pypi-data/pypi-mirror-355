from inspect import currentframe, getframeinfo
from colorama import Fore, Back
from datetime import datetime
import re
import pathlib
import colorama


class Logging:

    def __init__(self):

        self.max_len = 63

        self.clr_err = Fore.RED
        self.clr_warn = Fore.LIGHTYELLOW_EX
        self.clr_succ = Fore.LIGHTGREEN_EX

        self.clr_blue = Fore.BLUE
        self.clr_cyan = Fore.CYAN
        self.clr_magenta = Fore.MAGENTA

        self.clr_blue_light = Fore.LIGHTBLUE_EX
        self.clr_cyan_light = Fore.LIGHTCYAN_EX
        self.clr_magenta_light = Fore.LIGHTMAGENTA_EX

        self.clr_reset = Fore.RESET



    def print(self, txt: str | list[str], fore_color: None | list[Fore] | str = None, sep: str = '', end: str = '\n'):

        frameinfo = getframeinfo(currentframe().f_back)
        filename = re.split(r"[/|\\]", frameinfo.filename)[-1]
        linenumber = frameinfo.lineno
        now = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        str_prefix = f"{Fore.LIGHTBLACK_EX}{now} {self.clr_blue}{filename}:{linenumber}{Fore.RESET}"
        str_prefix += " " * (self.max_len - len(str_prefix))

        lst_txt = [txt] if not isinstance(txt, list) else txt
        lst_fore_color = [fore_color] if not isinstance(fore_color, list) else fore_color
        lst_content = list()

        for t, c in zip(lst_txt, lst_fore_color):
            str_suffix = re.sub('Completed', f'{self.clr_succ}Completed{self.clr_reset}', str(t))
            str_suffix = f"{c if c else ''}{str_suffix}{Fore.RESET}"
            lst_content.extend([str_suffix])


        str_content = f"{str_prefix} {sep.join(lst_content) if len(lst_content) > 1 else lst_content[0]}"

        print(str_content, end=end)





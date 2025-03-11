import colorama
import traceback
from datetime import datetime

colorama.init()

def get_current_time():
    return datetime.now().strftime('%m-%d %H:%M:%S')

def log_i(lg):
    print(colorama.Fore.WHITE + f'[{get_current_time()}] ' + colorama.Fore.GREEN + lg + colorama.Fore.RESET)

def log_d(lg):
    print(colorama.Fore.WHITE + f'[{get_current_time()}] ' + colorama.Fore.CYAN + lg + colorama.Fore.RESET)

def log_w(lg):
    print(colorama.Fore.WHITE + f'[{get_current_time()}] ' + colorama.Fore.YELLOW + lg + colorama.Fore.RESET)

def log_p(lg):
    print(colorama.Fore.WHITE + f'[{get_current_time()}] ' + colorama.Fore.WHITE + lg + colorama.Fore.RESET)

def log_e(lg):
    print(colorama.Fore.WHITE + f'[{get_current_time()}] ' + colorama.Fore.RED + lg + colorama.Fore.RESET)

def log_e_loc(lg):
    frame_info = traceback.extract_stack()[-2]
    filename = frame_info.filename
    lineno = frame_info.lineno
    print(colorama.Fore.WHITE + f'[{get_current_time()}] ' + colorama.Fore.RED + f'{filename}:{lineno} {lg}' + colorama.Fore.RESET)
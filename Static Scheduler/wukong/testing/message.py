class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[33m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    Red = '\033[91m'
    Green = '\033[92m'
    Blue = '\033[94m'
    Cyan = '\033[96m'
    White = '\033[97m'
    Yellow = '\033[93m'
    Magenta = '\033[95m'
    Grey = '\033[90m'
    Black = '\033[90m'
    Default = '\033[99m'

def err_msg(msg):
  return bcolors.FAIL + str(msg) + bcolors.ENDC

def warn_msg(msg):
  return bcolors.WARNING + str(msg) + bcolors.ENDC

def success_msg(msg):
  return bcolors.OKGREEN + str(msg) + bcolors.ENDC

def info_msg1(msg):
  return bcolors.OKCYAN + str(msg) + bcolors.ENDC

def info_msg2(msg):
  return bcolors.OKBLUE + str(msg) + bcolors.ENDC

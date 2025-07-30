from colorama import Fore

class LogType:
    SYSTEM = "SYSTEM"
    TRANSACTION = "TRANSACTION"
    SECURITY = "SECURITY"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    INTERNAL = "INTERNAL"
    DEPENDENCY = "DEPENDENCY"


class LogLevelColors:
    DEBUG = Fore.BLUE
    INFO = Fore.GREEN
    WARNING = Fore.YELLOW
    ERROR = Fore.RED
    CRITICAL = Fore.RED
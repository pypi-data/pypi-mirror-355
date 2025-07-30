LOG_FILE = [
    "Log file initialised (*)",
    "Python interpreter path: ",
    "Python version: *",
    "ParUtils version: *",
    "This will be logged in a file",
]
LOG_FILE_NOT = [
    "This won't be logged in a file",
]

N_W = len(LOG_FILE) + len(LOG_FILE_NOT)
WARNINGS = [
    "Expression 'This won't be logged in a file' couldn't be found in log file",
    "Expression 'Log file initialised (*)' was found in log file",
    "Expression 'Python interpreter path: ' was found in log file",
    "Expression 'Python version: *' was found in log file",
    "Expression 'ParUtils version: *' was found in log file",
    "Expression 'This will be logged in a file' was found in log file",
]
WARN = WARNINGS + [f"check_log LOG_FILE ended with {N_W} warnings"]
LEVEL_WARN_ERR = WARNINGS + [
    f"check_log LOG_FILE nok, too many warnings ({N_W} warnings)",
    f"[ttry] Exception caught match expected ('check_log LOG_FILE nok, too many warnings ({N_W} warnings)')",
]

LOG_INPUT = [
    "Test log input",
    "user command",
]

STEP_LOG = [
    "5 elements appended in * ms. 20 elements appended in total.",
    "Examples of duplicates (limited to 5)",
    "out_list: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]",
]

LOG_DICT = [
    "key1: value1",
    "key2: value2",
    "key3:",
    "  skey1: value1",
    "  skey2:",
    "    sskey1: value1",
    "    sskey2: value2",
    "    skey1: value1",
    "    skey2:",
    "        sskey1: value1",
    "        sskey2: value2",
    "	skey1: value1",
    "	skey2:",
    "		sskey1: value1",
    "		sskey2: value2",
]

ERR_HANDLING = [
    "Warning: the following message couldn't be logged because of [Errno 22] Invalid argument: ':.:.': * - test error handling normal 1",
    "Warning: the following message couldn't be logged because of [Errno 22] Invalid argument: ':.:.': * - test error handling normal 2",
    "* - test error handling normal 3",
]
ERR_HANDLING_NOT = [
    "test error handling max limit",
]

END_1 = [
    "check_log LOG_FILE ok",
    "check_log WARN ok",
    "check_log LOG_INPUT ok",
    "check_log UPDATE_LOGS ok",
]
END_2 = [
    "check_log LEVEL_WARN_ERR ok",
    "check_log STEP_LOG ok",
    "check_log LOG_DICT ok",
    "check_log ERR_HANDLING ok",
]

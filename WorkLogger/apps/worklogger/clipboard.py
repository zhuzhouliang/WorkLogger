__author__ = 'zhuzhou'

import win32clipboard
import time
import threading

import win32con


def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()

    return wrapper


class ClipboardMonitor:
    current_clip = ""
    interval = 1
    img_old_md5 = ''
    task_logger = None

    def __init__(self, task_logger):
        self.task_logger = task_logger

    def logClipboard(self):
        try:
            win32clipboard.OpenClipboard()
            raw_data = win32clipboard.GetClipboardData(win32con.CF_TEXT)
            self.task_logger.log_clipboard(raw_data)
        except Exception as e:
            # need to handle other non text format properly
            pass
        finally:
            win32clipboard.CloseClipboard()

    @threaded
    def run(self):
        s = ''
        while True:
            try:
                self.logClipboard()
                time.sleep(self.interval)
            except Exception as e:
                # logger.error(e.message)
                pass

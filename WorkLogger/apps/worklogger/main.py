__author__ = 'zhuzhou'
# -*- coding: utf-8 -*-

import time
import threading

import pythoncom
import pyHook

from worklogger import TaskLogger
from clipboard import ClipboardMonitor

RGT = '>'
LFT = '<'


def threaded(fn):
    def wrapper(*args, **kwargs):
        threading.Thread(target=fn, args=args, kwargs=kwargs).start()

    return wrapper


task_logger = TaskLogger()


class WindowMonitor:
    work_logger = None
    old_window_title = ''
    interval = 2

    def __init__(self, work_logger):
        # assert type(work_logger) is TaskLogger
        self.work_logger = work_logger

    @threaded
    def run(self):
        while True:
            try:
                task_logger.log_thinking_time_intervally()
                current_window_title = task_logger.get_current_window_title()
                if current_window_title == self.old_window_title:
                    pass
                else:
                    self.work_logger.change_window(current_window_title)
                    self.old_window_title = current_window_title

                time.sleep(self.interval)
            except Exception as e:
                # print str(e).encode('utf-8')
                #logger.trace('Window monitor error: '+str(e).encode('utf-8'))
                pass


last_special_key = ''


def OnKeyboardEvent(event):
    global last_special_key
    # print 'Ascii: %s, Key: %s, Extended: %s, Injected: %s, Alt: %s'% \
    # (str(event.Ascii),str(event.Key),str(event.Extended),str(event.Injected),str(event.Alt))
    # if special key is pressed
    if event.Ascii == 0:
        key = LFT + event.Key + RGT
        if event.Key == 'Return':
            key += '\n'
        if last_special_key != key:
            last_special_key = key
            task_logger.log_key_input(key)
        else:
            # Do we need to handle the time the one hold special key? It might provides some interesting
            # information
            pass
    else:
        if len(event.Key) > 1:
            task_logger.log_key_input(LFT + event.Key + RGT)
        else:
            task_logger.log_key_input(event.Key)
    return True


def OnKeyboardReleaseEvent(event):
    global last_special_key
    last_special_key = ''
    return True


def onClick(event):
    # Currently do not log the mouse click
    #task_logger.log_mouse_click(event.Position)
    return True


def start_key_logger():
    hm = pyHook.HookManager()
    hm.KeyDown = OnKeyboardEvent
    hm.KeyUp = OnKeyboardReleaseEvent
    hm.HookKeyboard()
    hm.SubscribeMouseAllButtonsDown(onClick)
    hm.HookMouse()
    print 'Started key logger'
    while True:
        try:
            pythoncom.PumpMessages()
        except KeyboardInterrupt:
            print 'Control C has been pressed'


if __name__ == "__main__":
    tl = WindowMonitor(task_logger)
    print 'Work logger started, will log your active window title into file: daily-work.log'
    tl.run()
    clip = ClipboardMonitor(task_logger)
    clip.run()
    start_key_logger()





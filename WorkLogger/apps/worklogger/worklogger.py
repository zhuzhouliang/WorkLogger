__author__ = 'zhuzhou'
import hashlib
import math
import datetime
import win32gui
import logging
import re
import os

from PIL import Image, ImageChops, ImageGrab

from configurer import WindowStrategy


SHORTEST_TITLE = 2
DAILY_WORK = 'daily-work'
handler = logging.FileHandler("daily-work.log")
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

RGT = '>'
LFT = '<'


class TaskLogger:
    '''

    '''
    keylogs = ':'
    SPACE = ' '
    last_mouse_click_position = None
    w = win32gui
    old_window_title = ""
    dict = {}
    screenshot_dict = {}
    timer = 0
    interval = 2
    SAVE_INTERVAL = 5
    to_save = SAVE_INTERVAL
    count = 1
    thinking_time = 1
    logged_content = ''
    logged_clipboard = ''

    window_strategy = WindowStrategy()

    def __unique_log(self, level, content):
        # print 'Logged content: %s'%self.logged_content
        # print 'Content:%s'%content
        if content != self.logged_content and not re.match('^\s*$', content):
            if level == 'error':
                logger.error(content)
            elif level == 'warn':
                logger.warn(content)
            elif level == 'info':
                logger.info(content)
            else:
                logger.debug(content)
            self.logged_content = content

    def log_thinking_time_intervally(self):
        self.thinking_time += 1

    def log_url(self):
        pass
        # Maybe it's best to do Alt+D to select url then copy to clipboard?

    def log_clipboard(self, clipboard_content):
        if self.logged_clipboard != clipboard_content:
            self.__unique_log("debug", "Clipboard:\n" + clipboard_content)
            self.logged_clipboard = clipboard_content

    def log_mouse_click(self, mouse_click_position):
        self.last_mouse_click_position = mouse_click_position
        self.__unique_log('debug', 'Mouse clicked at: ' + str(mouse_click_position))
        # print mouse_click_position

    def get_current_window_title(self):
        return self.w.GetWindowText(self.w.GetForegroundWindow())

    def repeat_to_length(self, char_to_repeat, length):
        return (char_to_repeat * ((length / len(char_to_repeat)) + 1))[:length]

    def log_key_input(self, key_input):
        # print 'Thinking time is: '+str(self.thinking_time)
        repeat_times = int(math.sqrt(self.thinking_time))
        self.keylogs += str(self.SPACE * repeat_times) + key_input

        if len(key_input) > 1 and self.window_strategy.need_capture(self.get_current_window_title(), key_input):
            print 'take screen shot'
            self.log_url()
            self.force_screenshot()
        #User typed something, so need to reset thinking time
        self.thinking_time = 1
        # print key_input

    def change_window(self, window_title):
        '''
        After window shift, need to clear the key input buffer
        :param window_title:
        :return:
        '''
        self.old_window_title = window_title
        if len(self.keylogs) > 1:
            self.__unique_log('debug', 'Keyboard input: \n' + self.keylogs)
            self.keylogs = ''
            self.thinking_time = 1
        # print 'Changed window: %s'%window_title
        self.__unique_log('info', "%s[%s]" % ("Change to window: ", window_title))


    def handle_save(self):
        self.to_save = self.to_save - self.interval
        if self.to_save <= 0:
            self.save_to_file()
            self.to_save = self.SAVE_INTERVAL


    def get_active_window_box(self):
        win = self.w.GetForegroundWindow()
        if self.w.GetWindowText(win) and len(self.w.GetWindowText(win)) > SHORTEST_TITLE:
            box = win32gui.GetWindowRect(win)
        else:
            # Seems no need to log the error, otherwise there are too many errors
            # logger.error('The window:<%s> could not be captured!' % (self.w.GetWindowText(win)))
            box = (0, 0, 800, 800)
        return box

    def get_url(self):
        pass

    def schedulely_screenshot(self):
        img = self._capture_current_window()
        if img:
            self._select_screen_to_save(img)

    def force_screenshot(self):
        box = self.get_active_window_box()
        img = ImageGrab.grab(box)
        if img:
            self._select_screen_to_save(img)

    def _capture_current_window(self):
        now = datetime.datetime.now()
        sec = now.second
        title = self.w.GetWindowText(self.w.GetForegroundWindow())
        inter = self._get_capture_interval_seconds(title)
        if sec % inter >= 0 and sec % inter < self.interval:
            box = self.get_active_window_box()
            return ImageGrab.grab(box)

    def __save_screen_update_dict(self, image, window_title):
        file_name = self.__save_captured_window(image, window_title)
        self.screenshot_dict[window_title] = file_name

    def _select_screen_to_save(self, image):
        window_title = self.old_window_title
        if window_title in self.screenshot_dict:
            if self._screenshot_changed_lot(window_title, image):
                self.__save_screen_update_dict(image, window_title)
        else:
            self.__save_screen_update_dict(image, window_title)

    def escape_special_in_path(self, string):
        s = re.sub(r'\W', '_', string)
        return s

    def __save_captured_window(self, image, window_title):
        t = str(datetime.datetime.now())
        file_name = self.escape_special_in_path(t + window_title) + '.png'
        image.save(os.path.join(DAILY_WORK, file_name))
        return file_name

    def __get_changed_area_from_image(self, box, image):
        wt, ht = image.size
        diff_img = None
        if box:
            bbox = (
                max(0, box[0]),
                max(0, box[1]),
                min(box[2], wt),
                min(box[3], ht))
            diff_img = image.crop(bbox)
            # logger.debug('Screenshot changed area: ' + str(bbox))
        return diff_img

    def __compare_images_to_bbox(self, image, old_image):
        old_image = old_image.convert('1')
        new_image = image.convert('1')
        diff = ImageChops.difference(new_image, old_image)
        box = diff.getbbox()
        return box

    def __check_if_changed_enough(self, diff_img, image, window_title):
        changed = False
        if diff_img:
            # diff_img.save(self.escape_special_in_path(window_title) + str(self.count) + ".PNG")
            # self.count += 1
            w, h = image.size
            w1, h1 = diff_img.size
            if (w * h) / (w1 * h1) < 4:
                changed = True
        return changed

    def _screenshot_changed_lot(self, window_title, image):
        changed = False
        if window_title in self.screenshot_dict:
            file_name = self.screenshot_dict[window_title]
            old_image = Image.open(os.path.join(DAILY_WORK, file_name))
            box = self.__compare_images_to_bbox(image, old_image)
            diff_img = self.__get_changed_area_from_image(box, image)
            changed = self.__check_if_changed_enough(diff_img, image, window_title)
        return changed

    def handle_image_clipboard(self):
        im = ImageGrab.grabclipboard()
        if im is None:
            im = ImageGrab.grab((0, 0, 500, 500))
        md5 = hashlib.md5(im.tostring()).hexdigest()
        img_file_name = 'Clipboard_image_' + str(md5) + '.png'
        if self.img_old_md5 != str(md5):
            im.save(os.path.join(DAILY_WORK, img_file_name), 'PNG')
            self.img_old_md5 = str(md5)
        return img_file_name
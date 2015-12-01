__author__ = 'zhuzhou'
import re


class WindowStrategy:
    _100_SECS_A_SHOT = 100
    SHORTEST_TITLE = 4

    window_and_action_dict = {
        ".+- Google Chrome": {"capture": ["<Snapshot>"]},
        ".+@.+:~": {"capture": ["<Snapshot>", "<Return>"]},
        ".+- Outlook": {"capture": ["<Snapshot>"]},
        ".+- Excel": {"capture": ["<Snapshot>"]},
        ".+- Word": {"capture": ["<Snapshot>"]},
        ".+PyCharm Community Edition.+": {"capture": ["<Snapshot>"]},
        r".+C:[\\/]+windows[\\/]+system32[\\/]+cmd[\\/.]+exe": {"capture": ["<Return>", "<Snapshot>"]}
    }

    screen_capture_seconds_dict = {
        ".+- Google Chrome": 10,
        ".+- Outlook": 100,
        ".+- Excel": 100,
        ".+- Word": 100,
        ".+PyCharm Community Edition.+": 2,
    }

    def need_capture(self, window_title, hotkey_name):
        # print hotkey_name
        if hotkey_name == '<Snapshot>':
            return True
        for key in self.window_and_action_dict:
            if re.match(key, window_title):
                strategy_dict = self.window_and_action_dict.get(key)
                if strategy_dict and "capture" in strategy_dict:
                    value_list = strategy_dict.get("capture")
                    if value_list and hotkey_name in value_list:
                        #print 'Matched hotkey'
                        return True
                    else:
                        pass
                        #print hotkey_name +' not in '+ str(value_list)
                else:
                    pass
                    #print 'no capture in strategy dict'
            else:
                pass
                #print key + ' can not match: '+window_title
        return False

    def _get_capture_interval_seconds(self, window_title):
        '''
        How frequently the window should be captured
        :param window_title:
        :return:
        '''
        if window_title and len(window_title) > self.SHORTEST_TITLE:
            for key in self.screen_capture_seconds_dict:
                if re.match(key, window_title):
                    return self.screen_capture_seconds_dict.get(key)
            return 10
        else:
            return self._100_SECS_A_SHOT
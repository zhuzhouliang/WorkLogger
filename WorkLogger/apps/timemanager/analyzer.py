__author__ = 'zhuzhou'
import ConfigParser
import re
import datetime
import collections


class LogGrouper:
    '''
    Constructor a dual key dict, the first key is the largest category of tasks, including task's category,
    for example: Writing Document/Coding/Writing Email/Searching
    And the second key is the keyword extract from the log like: Java/Python how to/XXX Design
    The value is the time each task costs

    2015-12-15 09:14:47,663 - INFO - Change to window: [Driver Support]
    2015-12-16 16:42:20,605 - INFO - Change to window: [time_ana.txt - xxx]
    '''
    SECONDS_IN_A_DAY = 24 * 60 * 60
    CATEGORY_DICT = {
        '(.+)- Google Search - Google Chrome': 'Searching',
        '(.+)- Stack Overflow - Google Chrome': 'Researching',
        '^InfoQ - (.+) - Google Chrome': 'Studying',
        '(.+)Managed Cloud': 'Discussion',
        'Conversation (.+)': 'Meeting',
        '(.+)- Outlook': 'Communication',
        '(.+)- Message \(HTML\)': 'Communication',
        '(.+)-\s+Notepad\+\+.+': 'Documentation',
        '(.+)- Eclipse': 'Coding',
        '(.+)\.py\s+-\s+.+\s+PyCharm Community Edition [.\d]+': 'Coding',
        '(.+)-\s*Excel': 'Documentation',
        '(.+)-\s*Word': 'Documentation',
        'JUDE\s*-\s*(.+)': 'Design',
    }
    REGEX_FOR_TIME = '^[-\d\s:]+'
    REGEX_FOR_TITLE = '.+to window:\s*\[(.+)\]\s*'
    last_time = None
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    category = 'IDLE'
    keywords = 'IDLE'
    title_time_dict = {}
    category_time_dict = {}

    def __init__(self):
        self.configParser = ConfigParser.RawConfigParser()

    def save(self, file_str):
        with open(file_str, 'w') as f:
            self.configParser.write(f)

    def swap_category_keywords(self, category, keywords):
        c = self.category
        k = self.keywords
        self.category = category
        self.keywords = keywords
        category = c
        keywords = k
        return category, keywords

    def save_to_file(self, category, keywords, time):
        if not self.configParser.has_section(category):
            self.configParser.add_section(category)
        if not self.configParser.has_option(category, keywords):
            self.configParser.set(category, keywords, 0)
        new_time = int(self.configParser.getint(category, keywords)) + int(time)
        self.configParser.set(category, keywords, new_time)

    def put(self, log_line):
        title, time = self.extract_title_and_time(log_line)
        title = title[::-1]
        if self.title_time_dict.get(title):
            old_time = self.title_time_dict[title]
            self.title_time_dict[title] = int(old_time) + int(time)
        else:
            self.title_time_dict[title] = int(time)

    def extract_title_and_time(self, log_line):
        '''
        Return three values: 1. category  2. keywords  3.time costed
        :param log_line:
        :return:
        '''
        time_costed = self.get_costed_time(log_line)
        title = self.get_title(log_line)
        return title, time_costed

    def extract_category_and_keywords(self, title):
        category, keywords = self.extract_title_info(title)
        return category, keywords

    def diff_time(self, now_time_str='2015-12-15 09:14:50', old_time_str='2015-12-15 09:14:00'):
        try:
            now = datetime.datetime.strptime(now_time_str, self.DATE_FORMAT)
            old = datetime.datetime.strptime(old_time_str, self.DATE_FORMAT)
            time_costed = (now - old).total_seconds()
        except:
            # TODO log the error
            time_costed = 0
        time_costed %= self.SECONDS_IN_A_DAY
        return time_costed


    def get_costed_time(self, log_line):
        time_diff = 0
        for time in re.findall(self.REGEX_FOR_TIME, log_line):
            if self.last_time:
                time_diff = self.diff_time(time, self.last_time)
            self.last_time = time
        return time_diff

    def get_title(self, log_line):
        m = re.match(self.REGEX_FOR_TITLE, log_line)
        title = 'UNTITLED'
        if m:
            title = m.group(1)
        return title

    def extract_title_info(self, title):
        category, keywords = '', ''
        for key in self.CATEGORY_DICT:
            matched = re.match(key, title)
            if matched:
                category = self.CATEGORY_DICT.get(key)
                keywords = matched.group(1)
                if keywords is None:
                    keywords = matched.group(0)
                return category, keywords
        return category, keywords

    def put_or_update(self, new_time, same_part):
        if self.category_time_dict.get(same_part):
            old_time = self.category_time_dict[same_part]
            self.category_time_dict[same_part] = int(old_time) + int(new_time)
        else:
            self.category_time_dict[same_part] = int(new_time)

    def convert_full_title_dict_to_category_dict(self):
        old_key = ''
        od = collections.OrderedDict(sorted(self.title_time_dict.items()))
        for k in od:
            same_part = self.get_same_part(old_key, k)
            new_time = od[k]
            if same_part == '':
                self.put_or_update(new_time, k)
            else:
                old_time = self.title_time_dict.get(old_key)
                self.put_or_update(new_time + old_time, same_part)
            old_key = k

    def get_same_part(self, s1, s2):
        same_part = ''
        for i in range(0, min(len(s1), len(s2))):
            if s1[0:i] == s2[0:i]:
                same_part = s1[0:i]
            else:
                break
        if same_part != '':
            same_part = same_part[0:same_part.rfind('-')]
        return same_part


if __name__ == '__main__':
    grouper = LogGrouper()
    with open('C:/Users/dev1/daily-work-test.log', 'r') as f:
        for line in f:
            grouper.put(line)
    grouper.convert_full_title_dict_to_category_dict()
    od = collections.OrderedDict(sorted(grouper.category_time_dict.items()))
    for key in od:
        grouper.save_to_file('All', key[::-1], grouper.category_time_dict[key])

    # od = collections.OrderedDict(sorted(grouper.title_time_dict.items()))
    # for key in od:
    # grouper.save_to_file('All', key[::-1], grouper.title_time_dict[key])

    grouper.save('c:/users/dev1/time_ana.txt')

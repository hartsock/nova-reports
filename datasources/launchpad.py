import urllib2
import json

__author__ = 'hartsocks'

PRIORITY_RANKS = {'LOW': 0, 'MEDIUM': 1, 'HIGH': 2, 'CRITICAL': 4}

class Tasks(object):
    def __init__(self, task_url):
        self._raw_data = Tasks.load_target(task_url)

    @staticmethod
    def load_target(target_url):
        file = urllib2.urlopen(target_url)
        return json.load(file)

    @staticmethod
    def rank_for(priority_name):
        return PRIORITY_RANKS.get(priority_name.upper(), 0)

    @property
    def priorities(self):
        p = []
        for entry in self._raw_data['entries']:
            p.append(entry['importance'])
        return p

    @property
    def rank(self):
        score = 0
        for priority in self.priorities:
            score = score + Tasks.rank_for(priority)
        return score

    @property
    def assignees(self):
        found = {}
        for entry in self._raw_data['entries']:
            link = entry.get('assignee_link')
            if not link is None:
                assignee = link[link.rfind('~'):]
                found[assignee] = link
        return found



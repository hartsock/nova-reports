import StringIO
import collections
import datasources.gerrit
import datasources.launchpad

from launchpadlib.launchpad import Launchpad

import sys

__author__ = 'hartsocks'

CACHE_DIR = '~/.launchpad_cache'

REPORT_COLUMNS = ['bug_id', 'url', 'priorities', 'rank', 'title', 'changes', 'owner', 'assignees']

Info = collections.namedtuple('Info', ['tasks', 'bug', 'changes'])
ReportLine = collections.namedtuple('ReportLine', REPORT_COLUMNS)

class Report(object):

    def __init__(self, **kwargs):
        self.gerrit_port = kwargs.pop('gerrit_port')
        self.trusted = kwargs.pop('trusted')
        self.tag = kwargs.pop('tag')

        query = kwargs.pop('query')
        if not query:
            project = kwargs.pop('project')
            self.query = "status:open project:%s" % project

            message_text = kwargs.pop('message_text')
            if message_text:
                self.query = "%s message:%s" % (self.query, message_text)

        else:
            self.query = query

        self.launchpad = Launchpad.login_anonymously(
            'anon', 'https://api.launchpad.net/', CACHE_DIR)

        self.categorizer = datasources.gerrit.Categorizer(self.trusted)
        self.gerrit = datasources.gerrit.Gerrit(self.query, self.gerrit_port, self.categorizer)
        self._data = []

    def tasks(self, bug_id):
        try:
            tasks_url = self.launchpad.bugs[bug_id].bug_tasks_collection_link
            bug_tasks = datasources.launchpad.Tasks(tasks_url)
            return bug_tasks
        except:
            return None

    def tags_for_bug(self, bug_id):
        try:
            bug = self.launchpad.bugs[bug_id]
            tags = bug.tags
            return tags
        except KeyError:
            return []

    def sort_report(self, key_lambda=None):
        if key_lambda is None:
            key_lambda = lambda line: line.rank * -1
        return sorted(self._data, key=key_lambda)

    def write(self, format, sort_key_lambda=None):
        for line in self.sort_report(sort_key_lambda):
            format(line)


class BugReport(Report):
    # a report that is bug centric

    def __init__(self,**kwargs):
        super(BugReport, self).__init__(**kwargs)
        bugs = {}
        for bug_id in self.gerrit.bugs:
            try:
                tags = self.tags_for_bug(bug_id)
                if self.tag in tags:
                    bug_tasks = self.tasks(bug_id)
                    bugs[bug_id] = Info(
                        changes = self.gerrit.get(bug_id),
                        bug = self.launchpad.bugs[bug_id],
                        tasks = bug_tasks)
            except KeyError:
                # could not find bug_id in launchpad
                print "could not find bug: %s" % bug_id
                pass

        report = []
        for bug_id in bugs.keys():
            info = bugs.get(bug_id)
            line = ReportLine(
                bug_id = bug_id,
                url = info.bug.web_link,

                priorities = info.tasks.priorities,
                rank = info.tasks.rank,
                title=info.bug.title,

                # change to list
                changes = info.changes,

                owner = info.bug.owner_link,
                assignees = info.tasks.assignees
            )
            report.append(line)

        self._data = report
        self._bugs = bugs

    @property
    def bug_ids(self):
        return self._bugs.keys()

    @property
    def report(self):
        return sorted(self._data, key=lambda line: line.rank * -1)

    def __str__(self):
        output = StringIO.StringIO()
        output.write(','.join(REPORT_COLUMNS))
        output.write('\n')

        for line in self.report:

            output.write(line.bug_id)
            output.write(' ,')

            output.write(line.url)
            output.write(' ,')

            output.write('/'.join(line.priorities))
            output.write(' ,')

            output.write(str(line.rank))
            output.write(' ,')

            for change in line.changes:
                output.write(change.url)

        return output.getvalue()

class ChangeReport(Report):

    def __init__(self, **kwargs):
        super(ChangeReport, self).__init__(**kwargs)
        self._data = self.gerrit.changes

    @property
    def changes(self):
        return self.gerrit.changes

    def filter_by_tag(self, tag):
        for change in self.changes:
            bugs = change.bugs
            for bug_id in bugs:
                tags = self.tags_for_bug(bug_id)
                if tag in tags:
                    yield change

    def changes_for_tag(self, tag, key_lambda=None):
        if not key_lambda:
            key_lambda = lambda change: change.age * -1

        changes = self.filter_by_tag(tag)
        return sorted(changes, key=key_lambda)

    def report_for_tag(self, tag, key_lambda, formatter):
        for change in self.changes_for_tag(tag, key_lambda):
            formatter(change)

    def bugs_for_change(self, change):
        bug_list = []
        bug_ids = change.bugs
        for bug_id in bug_ids:
            try:
                bug_list.append(self.launchpad.bugs[bug_id])
            except:
                pass
        return bug_list

    def priorities_for_change(self, change):
        out = []
        bug_ids = change.bugs
        for bug_id in bug_ids:
            tasks = self.tasks(bug_id)
            if tasks:
                for p in tasks.priorities:
                    out.append(p)
        return out
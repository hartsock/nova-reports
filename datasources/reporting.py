import StringIO
import collections
import datasources.gerrit
import datasources.launchpad

from launchpadlib.launchpad import Launchpad

import sys

__author__ = 'hartsocks'

CACHE_DIR = '~/.launchpad_cache'

REPORT_COLUMNS = ['bug_id', 'votes', 'url', 'change', 'priorities', 'rank', 'days_old', 'category', 'title', 'revision']

Info = collections.namedtuple('Info', ['tasks', 'bug', 'change'])
ReportLine = collections.namedtuple('ReportLine', REPORT_COLUMNS)

CATEGORIES = dict(unknown=-1, revise=0, review=1, core=2, approval=3)
CATEGORY_LIST = ['revise', 'review', 'core', 'approval']
# revise = has -1
# review = no votes

class Report(object):

    @staticmethod
    def has_trusted(voters, trusted):
        for trustee in trusted:
            if trustee in voters:
                return True

    @staticmethod
    def all_trusted(voters, trusted):
        for trustee in trusted:
            if not (trustee in voters):
                return False
        return True

    @staticmethod
    def categorize(vote_detail, trusted=None):
        if not trusted:
            trusted = []

        #trusted.append('jenkins')
        #trusted.append('smokestack')

        if 0 < len(vote_detail.get('-2', [])):
            return 'revise'

        if vote_detail.get('-1', []):
            return 'revise'

        category = 1
        if Report.has_trusted(vote_detail.get('1', []), trusted):
            if 2 < len(vote_detail.get('1',[])):
                category = 2
        elif 4 < len(vote_detail.get('1',[])):
            # 2 votes come from jenkins and smokestack
            category = 2

        if len(vote_detail.get('2', [])):
            category = 3

        return CATEGORY_LIST[category]

class BugReport(object):
    def __init__(self,**kwargs):
        gerrit_port = kwargs.pop('gerrit_port')
        trusted = kwargs.pop('trusted')
        tag = kwargs.pop('tag')
        project = kwargs.pop('project')
        message_text = kwargs.pop('message_text')

        query = "status:open project:%s" % project
        if message_text:
            query = "%s message:%s" % (query, message_text)

        launchpad = Launchpad.login_anonymously(
            'anon', 'https://api.launchpad.net/', CACHE_DIR)

        bugs = {}
        gerrit = datasources.gerrit.Gerrit(query, gerrit_port)
        for bug_id in gerrit.bugs:
            try:
                bug = launchpad.bugs[bug_id]
                tags = bug.tags
                if tag in tags:
                    tasks_url = launchpad.bugs[bug_id].bug_tasks_collection_link
                    bug_tasks = datasources.launchpad.Tasks(tasks_url)
                    bugs[bug_id] = Info(
                        change = gerrit.get(bug_id),
                        bug = launchpad.bugs[bug_id],
                        tasks = bug_tasks)
            except KeyError:
                # could not find bug_id in launchpad
                print "could not find bug: %s" % bug_id
                pass

        report = []
        for bug_id in bugs.keys():
            info = bugs.get(bug_id)
            votes_summary = gerrit.votes(bug_id)
            line = ReportLine(
                bug_id = bug_id,
                votes = votes_summary,
                url = info.bug.web_link,
                change = gerrit.get_url(bug_id),
                priorities = info.tasks.priorities,
                rank = info.tasks.rank,
                days_old = gerrit.days_old(bug_id),
                category = Report.categorize(votes_summary, trusted),
                title=info.bug.title,
                revision=gerrit.change_last_revision_number(info.change)
            )
            report.append(line)

        self._report = report
        self._bugs = bugs
        self._launchpad = launchpad
        self._gerrit = gerrit

    @property
    def bug_ids(self):
        return self._bugs.keys()

    @property
    def report(self):
        return sorted(self._report, key=lambda line: line.rank * -1)

    def sort_report(self, key_lambda=None):
        if key_lambda is None:
            key_lambda = lambda line: line.rank * -1
        return sorted(self._report, key=key_lambda)

    @property
    def gerrit(self):
        return self._gerrit

    @property
    def launchpad(self):
        return self._launchpad

    @staticmethod
    def vote_summary(votes):
        vote_summary = {
            '-2': len(votes.get('-2', [])),
            '-1': len(votes.get('-1', [])),
            '1': len(votes.get('1', [])),
            '2': len(votes.get('2', []))
        }
        return vote_summary

    def write(self, format, sort_key_lambda=None):
        for line in self.sort_report(sort_key_lambda):
            format(line)

    def __str__(self):
        output = StringIO.StringIO()
        output.write(','.join(REPORT_COLUMNS))
        output.write('\n')

        for line in self.report:
            vote_summary = BugReport.vote_summary(line.votes)

            output.write(line.bug_id)
            output.write(' ,')

            output.write(str(vote_summary))
            output.write(' ,')

            output.write(line.url)
            output.write(' ,')

            output.write(line.change)
            output.write(' ,')

            output.write('/'.join(line.priorities))
            output.write(' ,')

            output.write(str(line.rank))
            output.write(' ,')

            output.write(str(line.days_old))
            output.write(' ,')

            output.write(line.category)
            output.write('\n')

        return output.getvalue()

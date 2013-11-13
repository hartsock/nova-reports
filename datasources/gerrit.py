
import json
import os
import re
import copy

from datetime import date

__author__ = 'hartsocks'

LOAD_COMMAND = 'ssh  -p %s review.openstack.org gerrit query --format json --all-approvals --dependencies --files --commit-message --comments "%s"  2>&1 | grep -v runTimeMilliseconds'

# queries all open review requests.

# references:
# https://review.openstack.org/Documentation/json.html
class Gerrit(object):

    def __init__(self, query, port, categorizer=None):
        self._changes = []
        self._bug_ids = []
        self._blueprint_ids = []
        command = LOAD_COMMAND % (port, query)
        raw_data_handle = os.popen(command)
        for raw_data in raw_data_handle.readlines():
            json_row = json.loads(raw_data)
            message = json_row['commitMessage']
            bugs = Gerrit.bugs_from_comment(message)
            bps = Gerrit.bps_from_comment(message)
            json_row['bugs'] = bugs
            for bug_id in bugs:
                self._bug_ids.append(bug_id)
            change = Change(json_row, bugs, bps, self, categorizer)
            self._changes.append(change)

    def get(self, bug_id):
        return [c for c in self._changes if c.for_bug(bug_id)]

    def get_url(self, bug_id):
        return set([c['url'] for c in self.get(bug_id)])

    def changes_for(self, path_phrase='vmware'):
        list = []
        for row in self._changes:
            if row.touches_file_name(path_phrase):
                list.append(row)
        return list

    @property
    def changes(self):
        return self._changes

    @property
    def count(self):
        return len(self._changes)

    @property
    def vmware_changes(self):
        return self.changes_for('/vmwareapi/')

    @property
    def bugs(self):
        return self._bug_ids

    @property
    def data(self):
        return self._changes[:]

    @staticmethod
    def bug_from_comment(comment):
        expr = u'.*(\w*.bug|bug|lp|lp#)\D*(\d{1,}).*'
        res = re.compile(expr, re.IGNORECASE).search(comment)
        if res:
            return res.group(2)

    @staticmethod
    def bp_from_comment(comment):
        expr = u'.*\s(bp/\w+)\W?.*'
        res = re.compile(expr, re.IGNORECASE).search(comment)
        if res:
            return res.group(1)

    @staticmethod
    def _filter_by_line(comment, filter):
        out = []
        lines = comment.split('\n')
        for line in lines:
            val = filter(line)
            if val:
                out.append(val)
        return out

    @staticmethod
    def bugs_from_comment(comment):
        return Gerrit._filter_by_line(
            comment, Gerrit.bug_from_comment)

    @staticmethod
    def bps_from_comment(comment):
        return Gerrit._filter_by_line(
            comment, Gerrit.bp_from_comment)


class Change(object):

    def __init__(self, change, bugs, blueprints, gerrit, categorizer):
        self._change = change
        self._bugs = bugs
        self._blueprints = blueprints
        self._gerrit = gerrit
        self._categorizer = categorizer
        self._last_patchset = None
        self._first_patchset = None

    def __len__(self):
        return self._change.__len__()

    def __getitem__(self, key):
        return self._change.get(key)

    def __iter__(self):
        self._change.__iter__()

    def __contains__(self, item):
        self._change.__contains__(item)

    @property
    def json(self):
        return copy.deepcopy(self._change)

    @property
    def bugs(self):
        return set(self._bugs)

    @property
    def blueprints(self):
        return set(self._blueprints)

    def for_bug(self, bug_id):
        return bug_id in self._bugs

    @property
    def url(self):
        return self._change['url']

    def filter_patchsets(self, patchsets, filter):
        found = None
        for current in patchsets:
            if filter(current, found):
                found = current
        return copy.deepcopy(found)

    @property
    def last_patchset(self):
        if not self._last_patchset:
            filter = lambda next,last: last is None or int(next['number']) > int(last['number'])
            patchsets = self.json['patchSets']
            self._last_patchset = self.filter_patchsets(patchsets, filter)
        return copy.deepcopy(self._last_patchset)

    @property
    def first_patchset(self):
        if not self._first_patchset:
            filter = lambda next,last: last is None or next['createdOn'] < last['createdOn']
            patchsets = self.json['patchSets']
            self._first_patchset = self.filter_patchsets(patchsets, filter)
        return copy.deepcopy(self._first_patchset)

    @property
    def votes(self):
        patchset = self.last_patchset
        v = dict(bugs=self.bugs)
        v['patchset_number'] = patchset['number']
        for approval in patchset.get('approvals', []):
            vote = dict(
                email=approval['by'].get('email'),
                username=approval['by'].get('username'),
                value=approval['value']
            )
            approvers = v.get(approval['value'], [])
            approver = vote['email']
            if vote['email'] is None:
                approver = vote['username']
            approvers.append(approver)
            v[approval['value']] = approvers
        return v

    @property
    def vote_summary(self):
        votes = self.votes
        vote_summary = {
            '-2': len(votes.get('-2', [])),
            '-1': len(votes.get('-1', [])),
            '1': len(votes.get('1', [])),
            '2': len(votes.get('2', []))
        }
        return vote_summary

    @property
    def files(self):
        list = []
        patchset = self.last_patchset
        for json in patchset['files']:
            list.append(json['file'])
        return list

    @property
    def revision(self):
        patchset = self.last_patchset
        return patchset['number']

    def calculate_age(self, timestamp):
        created = date.fromtimestamp(timestamp)
        now = date.today()
        age = now - created
        return age.days

    @property
    def last_updated(self):
        last_updated = self.json['lastUpdated']
        return self.calculate_age(last_updated)

    @property
    def age(self):
        patchset = self.last_patchset
        timestamp = patchset['createdOn']
        approvals = [a for a in patchset.get('approvals',[]) if a['by'].get('username', 'nobody') == 'jenkins']
        if approvals:
            timestamp = approvals[0]['grantedOn']
        return self.calculate_age(timestamp)

    @property
    def total_age(self):
        patchset = self.first_patchset
        return self.calculate_age(patchset['createdOn'])

    @property
    def category(self):
        if not self._categorizer:
            return 'uncategorized'
        return self._categorizer.categorize(self)

    @property
    def title(self):
        tail = ""
        message = self.json['commitMessage']
        i = message.find('\n\n')
        if 60 < i:
            i = 57
            tail = "..."
        return message[:i] + tail

    def touches_file_name(self, file_name):
        for json in self.last_patchset['files']:
            if file_name in json['file']:
                return True
        return False


class Categorizer(object):

    def __init__(self, trusted):
        self._trusted = trusted
        self._categories = dict(unknown=-1, revise=0, review=1, core=2, approval=3)
        self._category_list = ['revise', 'review', 'core', 'approval']

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

    def categorize(self, change):
        trusted = self._trusted
        if not trusted:
            trusted = []

        vote_detail = change.votes

        if 0 < len(vote_detail.get('-2', [])):
            return 'revise'

        if vote_detail.get('-1', []):
            return 'revise'

        category = 1
        if Categorizer.has_trusted(vote_detail.get('1', []), trusted):
            if 2 < len(vote_detail.get('1',[])):
                category = 2
        elif 4 < len(vote_detail.get('1',[])):
            # 2 votes come from jenkins
            category = 2

        if len(vote_detail.get('2', [])):
            category = 3

        return self._category_list[category]
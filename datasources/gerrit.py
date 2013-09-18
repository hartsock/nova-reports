
import json
import os
import re

from datetime import date
from pickle import dumps

__author__ = 'hartsocks'

LOAD_COMMAND = 'ssh  -p %s review.openstack.org gerrit query --format json --all-approvals --dependencies --files --commit-message --comments "%s"  2>&1 | grep -v runTimeMilliseconds'

# queries all open review requests.

# references:
# https://review.openstack.org/Documentation/json.html
class Gerrit(object):

    def __init__(self, query, port):
        #TODO(hartsocks): this should be rewritten without the _reviews map
        self._reviews = {}
        self._data = []
        self._bug_ids = []
        command = LOAD_COMMAND % (port, query)
        raw_data_handle = os.popen(command)
        for raw_data in raw_data_handle.readlines():
            json_row = json.loads(raw_data)
            message = json_row['commitMessage']
            bugs = Gerrit.bugs_from_comment(message)
            json_row['bugs'] = bugs
            for bug_id in bugs:
                self._bug_ids.append(bug_id)
                # TODO(hartsocks): this block is bad, rewrite
                if self._reviews.has_key(bug_id):
                    # allow a list of changes since one bug
                    # may inspire multiple change sets
                    prev = self._reviews[bug_id]
                    next = [prev]
                    if isinstance(prev, list):
                        # whoops, prev is already a list
                        next = prev
                    # builds up a list of changes per bug
                    next.append(json_row)
                    self._reviews[bug_id] = next
                self._reviews[bug_id] = json_row
            self._data.append(json_row)

    def get(self, bug_id):
        return self._reviews.get(bug_id)

    def get_url(self, bug_id):
        return self.get(bug_id)['url']

    def votes(self, bug_id):
        v = dict(bug_id=bug_id)
        patchset = self.latest_patchset(bug_id)
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

    def latest_patchset(self, bug_id):
        change = self.get(bug_id)
        return self.last_patchset(change)

    def files(self, bug_id):
        list = []
        patchset = self.latest_patchset(bug_id)
        for json in patchset['files']:
            list.append(json['file'])
        return list

    def has_vmwareapi_file(self, bug_id):
        return self.has_vmwareapi_file(bug_id, '/vmwareapi/')

    def has_file_path(self, bug_id, phrase='vmware'):
        for json in self.latest_patchset(bug_id)['files']:
            if phrase in json['file']:
                return True

    def check_files(self, json_row, phrase='vmware'):
        patchset = self.last_patchset(json_row)
        for entry in patchset['files']:
            if phrase in entry['file']:
                return True

    def changes_for(self, path_phrase='vmware'):
        list = []
        for row in self._data:
            if self.check_files(row, path_phrase):
                list.append(row)
        return list

    def patch_set_age(self, patchset):
        created_on = patchset['createdOn']
        created = date.fromtimestamp(created_on)
        now = date.today()
        age = now - created
        return age.days

    def days_old(self, bug_id):
        patchset = self.latest_patchset(bug_id)
        return self.patch_set_age(patchset)

    def change_age_last_revision(self, change):
        """
        Calculate change sets' age by using
        the last uploaded patch set.
        """
        patchset = self.last_patchset(change)
        return self.patch_set_age(patchset)

    def last_patchset(self, change):
        patchset = change['patchSets'][-1]
        for pset in change['patchSets']:
            if pset['number'] > patchset['number']:
                patchset = pset
        return patchset

    @property
    def count(self):
        return len(self._data)

    @property
    def vmware_changes(self):
        return self.changes_for('/vmwareapi/')

    @property
    def bugs(self):
        return self._bug_ids

    @property
    def data(self):
        return self._data[:]

    @staticmethod
    def bug_from_comment(comment):
        expr = u'.*(fixes\s\w+|bug|lp|lp#)\D*(\d{1,}).*'
        res = re.compile(expr, re.IGNORECASE).search(comment)
        if res:
            return res.group(2)

    @staticmethod
    def bugs_from_comment(comment):
        bugs = []
        lines = comment.split('\n')
        for line in lines:
            bug = Gerrit.bug_from_comment(line)
            if bug:
                bugs.append(bug)
        return bugs
import unittest
import datasources.gerrit

__author__ = 'hartsocks'

class TestGerritQuery(unittest.TestCase):
    def test_bug_from_comment(self):
        comment = """
        This is a long multiline comment.
        This is a long multiline comment.

        bug 123

        This is a long multiline comment.
        This is a long multiline comment.
        """

        bug = datasources.gerrit.Gerrit.bug_from_comment(comment)
        print bug
        self.assertEqual(bug, "123", "did not parse properly")

    def test_bugs_from_comment(self):
        comment = """
        This is a long multiline comment.
        This is a long multiline comment.

        bug 123

        This is a long multiline comment.
        This is a long multiline comment.
        something bug 456 something else.
        """

        bugs = datasources.gerrit.Gerrit.bugs_from_comment(comment)
        print bugs
        self.assertEqual(['123', '456'], bugs)

    def test_lp_from_comment(self):
        comment = """
        This is a long multiline comment.
        This is a long multiline comment.

        Fixes LP #123

        This is a long multiline comment.
        This is a long multiline comment.
        something bug 456 something else.
        """

        bugs = datasources.gerrit.Gerrit.bugs_from_comment(comment)
        print bugs
        self.assertEqual(['123', '456'], bugs)

    def test_lp_format_from_comment(self):
        comment = """
        This is a long multiline comment.
        This is a long multiline comment.

        LP# 123

        This is a long multiline comment.
        This is a long multiline comment.
        something bug 456 something else.
        """

        bugs = datasources.gerrit.Gerrit.bugs_from_comment(comment)
        print bugs
        self.assertEqual(['123', '456'], bugs)

    def test_lp_hard_from_comment(self):
        comment = """
[VMware] Fix problem transferring files with ipv6 host

Need to protect the host name with '[' and ']' before
we create a http/https connection

Fixes LP# 1224479

Change-Id: I8c2e58d3eb5e001eff3c9354c3cdc593469b23ac"""
        bugs = datasources.gerrit.Gerrit.bugs_from_comment(comment)
        print bugs
        self.assertEqual(['1224479'], bugs)

    def test_closes_hard_from_comment(self):
        comment = """
[VMware] Fix problem transferring files with ipv6 host

Need to protect the host name with '[' and ']' before
we create a http/https connection

Fixes: bug #1207064
Closes-LP# 1224479
Fixes-bug: 123456
obliterates-lp #654321

Change-Id: I8c2e58d3eb5e001eff3c9354c3cdc593469b23ac"""
        bugs = datasources.gerrit.Gerrit.bugs_from_comment(comment)
        print bugs
        self.assertEqual(['1207064', '1224479', '123456', '654321'], bugs)

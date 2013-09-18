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
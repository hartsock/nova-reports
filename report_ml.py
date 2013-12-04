import datasources.reporting
import datetime
from optparse import OptionParser

__author__ = 'hartsocks'

parser = OptionParser()
parser.add_option("-f", "--format", dest="report_format", default="email",
                  help="generate a report in a given format")
parser.add_option("-t", "--tag", dest="tag", default="vmware",
                  help="generate a report for a tag")
parser.add_option("-p", "--project", dest="project_name", default="openstack/nova",
                  help="generate a report for a project")
parser.add_option("-m", "--message", dest="gerrit_message", default=None,
                  help="text to look for in gerrit messages")
parser.add_option("-l", "--trusted-list", dest="trusted_list_str", default="",
                  help="list of trusted reviewers, comma delimited")
parser.add_option("-g", "--gerrit-port", dest="gerrit_port",
                  help="Port number to use when working with gerrit via ssh.")
(options, args) = parser.parse_args()

print "Starting report run..."
print
print datetime.date.today()
print

bug_report = datasources.reporting.BugReport(
    trusted=options.trusted_list_str.split(','),
    tag=options.tag,
    project=options.project_name,
    message_text=options.gerrit_message,
    gerrit_port=options.gerrit_port
)

cat = dict(unknown=1, revise=0, review=-1, core=-2, approval=-3)
titles = dict(
    unknown="other",
    revise="needs revision",
    review="needs review",
    core="ready for core",
    approval="needs one more +2/approval")

print "Ordered by bug priority:"
def short_format(line):
    categories = [titles.get(change.category, ' ? ') for change in line.changes]
    print "* %s, %s : '%s' \n\t %s" % (
        '/'.join(line.priorities), ','.join(categories),  line.title,
        '\n\t '.join([ "%s" % (change.url) for change in line.changes]),)

print "{|"
bug_report.write(short_format)
print "|}"

print
print "-" * 80

change_report = datasources.reporting.ChangeReport(
    trusted=options.trusted_list_str.split(','),
    tag=options.tag,
    project=options.project_name,
    message_text=options.gerrit_message,
    gerrit_port=options.gerrit_port
)
print "Ordered by fitness for review:"

last_category = None
def long_format(change):
    global last_category
    if change.category != last_category:
        print
        print "== %s ==" % titles[change.category]
        last_category = change.category
    v = change.vote_summary
    print "* %s" % change.url
    print "\ttitle: '%s'" % change.title
    print "\tvotes: +2:%s, +1:%s, -1:%s, -2:%s." % (v.get('2',0), v.get('1',0), v.get('-1',0), v.get('-2', 0)),
    print "+%s days in progress, revision: %s is %s days old " % (change.total_age, change.revision, change.age)

change_report.report_for_tag('vmware', lambda change: change.category, long_format)

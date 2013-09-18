import datasources.reporting
from optparse import OptionParser

__author__ = 'hartsocks'

parser = OptionParser()
parser.add_option("-f", "--format", dest="report_format", default="email",
                  help="generate a report in a given format")
parser.add_option("-t", "--tag", dest="tag", default="vmware",
                  help="generate a report for a tag")
parser.add_option("-p", "--project", dest="project_name", default="openstack/nova",
                  help="generate a report for a project")
parser.add_option("-m", "--message", dest="gerrit_message", default="bug",
                  help="text to look for in gerrit messages")
parser.add_option("-l", "--trusted-list", dest="trusted_list_str", default="",
                  help="list of trusted reviewers, comma delimited")
parser.add_option("-g", "--gerrit-port", dest="gerrit_port",
                  help="Port number to use when working with gerrit via ssh.")
(options, args) = parser.parse_args()

report = datasources.reporting.BugReport(
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

print "Ordered by priority:"
def short_format(line):
    print "* %s %s %s readiness:%s" % ( '/'.join(line.priorities), line.url, line.change, titles.get(line.category, '?'))
    #print "** %s " % line.title
report.write(short_format)
print
print "-" * 80
print "Ordered by fitness for review:"

last_category = None
def long_format(line):
    global last_category
    if line.category != last_category:
        print
        print titles[line.category]
        last_category = line.category
    v = datasources.reporting.BugReport.vote_summary(line.votes)
    print "* %s %s review: %s" % ('/'.join(line.priorities), line.url, line.change)
    print "\ttitle: '%s'" % line.title
    print "\tvotes: +2:%s, +1:%s, -1:%s, -2:%s" % (v.get('2',0), v.get('1',0), v.get('-1',0), v.get('-2', 0)),
    print " age: %s days" % (line.days_old)

report.write(long_format, lambda line: cat[line.category] )
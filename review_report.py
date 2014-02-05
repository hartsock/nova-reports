import datasources.reporting
import datetime
from optparse import OptionParser

__author__ = 'hartsocks'

parser = OptionParser()
parser.add_option("-f", "--filename", dest="filename", default="vmware",
                  help="generate a report for a filename pattern")
parser.add_option("-q", "--query", dest="query", default="is:open project:openstack/nova",
                  help="query for gerrit")
parser.add_option("-g", "--gerrit-port", dest="gerrit_port",
                  help="Port number to use when working with gerrit via ssh.")
(options, args) = parser.parse_args()

print "Starting release report run..."
print
print datetime.date.today()
print
print "-" * 80

change_report = datasources.reporting.ChangeReport(
    gerrit_port=options.gerrit_port,
    query=options.query
)

#change_report.report_for_tag('vmware', lambda change: change.category, long_format)
count = 0
def long_format(change):
    global count
    count = count + 1
    print "%03d, %s , %s , %s " % (count, change.url, change.title, change.last_updated_date)

change_report.report_for_filename(options.filename, lambda change: change.age, long_format)

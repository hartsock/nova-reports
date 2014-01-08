import datasources.gerrit
from optparse import OptionParser

__author__ = 'hartsocks'

parser = OptionParser()
parser.add_option("-q", "--query")
parser.add_option("-p", "--path", dest="path_string", default="vmware",
                  help="look for path fragment in patches", metavar="CHANGE_PATH_FRAGMENT")
parser.add_option("-g", "--gerrit-port", dest="gerrit_port",
                  help="Port number to use when working with gerrit via ssh.")
(options, args) = parser.parse_args()

path_string = options.path_string
# query gerrit's open reviews for a list of changes
gerrit = datasources.gerrit.Gerrit("status:open",options.gerrit_port)
print "Total change count:"
print gerrit.count
print "A list of changes that touch files with '%s' in their path names" % path_string
count = 0
for change in gerrit.changes_for(path_string):
    print "* %s " % change['url']
    count += 1
print "Changes: %s" % count
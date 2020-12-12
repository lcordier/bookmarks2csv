#!/usr/bin/env python

""" Extract Firefox places.sqlite (bookmarks) database to CSV file.

    https://python-catalin.blogspot.com/2019/03/get-bookmarks-from-your-firefox-browser.html
"""
import csv
import datetime
import optparse
import os
import sqlite3
import sys


# Windows: 'C:/Users/YOUR_WINDOWS_ACCOUNT/AppData/Roaming/Mozilla/Firefox/'
FIREFOX_HOME = '~/.mozilla/firefox/'

# Output field order.
ORDER = [
    'url',
    'title',
    'description',
    'rev_host',
    'frecency',
    'last_visited',
    'date_added'
]


def as_dicts(cursor):
    """ Return a list of dictionaries from a result-set.
    """
    fields = [k[0] for k in cursor.description]
    result = []
    rows = cursor.fetchall()
    for row in rows:
        result.append(dict(zip(fields, row)))

    return result


def extract_bookmarks(cursor, writer):
    query = """
        SELECT url,
               MP.title,
               description,
               rev_host,
               frecency,
               last_visit_date AS last_visited,
               dateAdded AS date_added

            FROM moz_places MP
                JOIN moz_bookmarks MB
                ON MB.fk = MP.id

            WHERE visit_count>0
              AND MP.url like 'http%'
            ORDER BY dateAdded DESC;
    """
    try:
        cursor.execute(query)
    except Exception as e:
        print(str(e))
    else:
        writer.writerow(ORDER)
        for rec in as_dicts(cursor):
            rec['last_visited'] = datetime.datetime.fromtimestamp(rec['last_visited'] / 1000000.0).replace(microsecond=0)
            rec['date_added'] = datetime.datetime.fromtimestamp(rec['date_added'] / 1000000.0).replace(microsecond=0)
            writer.writerow([rec[field] for field in ORDER])


if __name__ == '__main__':

    parser = optparse.OptionParser()

    parser.add_option('-p',
                      '--places',
                      dest='places',
                      action='store',
                      type='string',
                      default='',
                      help='path to firefox bookmarks database (places.sqlite)')

    parser.add_option('-o',
                      '--output',
                      dest='output',
                      action='store',
                      type='string',
                      default='bookmarks.csv',
                      help='output filename [bookmarks.csv]')

    options, args = parser.parse_args()

    places = options.places
    output = open(options.output, 'w')
    writer = csv.writer(output, quoting=csv.QUOTE_ALL, lineterminator='\n')

    if not places:
        print('No places.sqlite specified, try any of these:\n')
        for root, dirs, files in os.walk(os.path.expanduser(FIREFOX_HOME)):
            if '.default' in root and 'places.sqlite' in files:
                print(os.path.join(root, 'places.sqlite'))

        print('')
        parser.print_help()
        sys.exit()

    if os.path.exists(places):
        connection = sqlite3.connect(places)
        cursor = connection.cursor()
        extract_bookmarks(cursor, writer)
        cursor.close()
        output.close()


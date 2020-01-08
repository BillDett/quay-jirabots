import os
import sys
import logging
import json
import requests
from requests.auth import HTTPBasicAuth

# Backlog Bot
#  Closes old Backlog items that haven't been updated in a long time.
# BE CAREFUL WITH THIS CODE- you could accidentally close the whole backlog if you are not careful!
    
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

username = os.getenv('USERNAME')
if not username:
    logging.critical('Need to specify USERNAME')
    sys.exit(1)

password = os.getenv('PASSWORD')
if not password:
    logging.critical('Need to specify PASSWORD')
    sys.exit(1)

host = os.environ.get('JIRA_HOST', 'https://issues.redhat.com')

age = os.environ.get('AGE', '-365d')        # What age issues should we look at?
updated = os.getenv('UPDATED', '-90d')      # How long since last update to be considered for closure?
dryrun = os.environ.get('DRYRUN')           # Should we just report on what would be closed and not actually close them?

logging.info('Reviewing Backlog on ' + host + ' for items created earlier than ' + age + ' and not updated in ' + updated)
if dryrun:
    logging.info('Running read-only- no changes will be made')

jql = "project=PROJQUAY+and+status=open+and+createdDate<'" + age + "'+and+updatedDate<'" + updated + "'"
#jql = "project=PROJQUAY+and+key=PROJQUAY-1"    # For testing purposes
max_results = '&maxResults=100'
url = host + '/rest/api/latest/search?jql=' + jql + max_results

r = requests.get(url, auth=HTTPBasicAuth(username, password))
if r.status_code != requests.codes.ok:
    logging.error('Problem fetching issues: \n' + r.text)
    r.raise_for_status()

responsejson = r.json()

logging.info('Found ' + str(responsejson['total']) + ' issues to be closed.')

payload = {
  'update': {
        'comment': [
         {
            'add': {
               'body': 'This issue has been automatically closed due to inactivity.  Please re-open the issue if necessary.'
            }
         }
      ]
  },
  'transition': {
    'id': '2'
  }
}

headers = { 'Content-Type': 'application/json'}
for issue in responsejson['issues']:
    logging.info('Closing ' + issue['key'])
    url = host + '/rest/api/latest/issue/' + issue['key'] + '/transitions'
    if not dryrun:
        r = requests.post(url, json=payload, auth=HTTPBasicAuth(username, password))
        if r.status_code != 204:
            logging.error('Problem closing issue ' + issue['key'] + ':\n' + r.text)

logging.info('Done closing issues in backlog')
#!/usr/bin/python
##
## This script will convert the data
## from the astronomy website
## (http://www.seasky.org) to ical
## The content of seasky.org is
## copyrighted.
## NOTE: this script is licensed under MIT
##
## Author: Mehdi Nellen, Tuebingen 2015

import urllib3
import re
from bs4 import BeautifulSoup
from icalendar import *
from datetime import datetime, date, time, timedelta


months = {'January': 1,
          'February': 2,
          'March': 3,
          'April': 4,
          'May': 5,
          'June': 6,
          'July': 7,
          'August': 8,
          'September': 9,
          'October': 10,
          'November': 11,
          'December': 12}
# specify the range of years you would like to have. SeaSky has the calendars up tp 2030 at this time.
# but dont forget to add 1 to the last year
years = [2022, 2031]
ical_f='astroCal.ics'

def getDate(li, year):
    '''retrieves the date from "li"
       by combining it with "year"
       it may also return multiple dates
       depending on the content'''
    # print remove commas, split the string to only get the month and day in a list
    splitD = list(filter(None, re.sub(",", "", li.p.text).split("-")[0].split(" ")))
    # save the date(s) into a list
    result_date   = [ date(year, months[splitD[0]], int(day)) for day in splitD[1:] ]
    return result_date


def getSumm(li):
    '''retrieves the summary from "li"'''
    splitD = li.p.text.split("-")[1].split(".")[0].strip()
    return splitD

def getDescr(li):
     ''' retrieves the description from "li" '''
     splitD = (".".join(li.p.text.split(".")[1:])).strip()
     # seasky should be credited for their work
     splitD = splitD + " (copyright: http://www.seasky.org)"
     return splitD

def saveIcal(cal):
    ''' Save the cal into a file '''
    ical_handle = open(ical_f, 'wb')
    ical_handle.write(cal.to_ical())
    ical_handle.close()
    print('saved as %s'%ical_f)

def initCal():
    ''' creates the header of the ical '''
    cal = Calendar()
    cal.add('version', '2.0')
    cal.add('prodid', '-//Astronomical events//seasky.org//')
    cal.add('x-wr-calname', 'AstroEvents')
    cal.add('X-WR-TIMEZONE', 'Europe/Amsterdam')
    newtimezone = Timezone()
    newtimezone.add('tzid', "Europe/Amsterdam")
    cal.add_component(newtimezone)

    return cal

def extractTime(description, date):
    ''' extract time from description '''
    match = re.search('(\d\d):(\d\d) UTC', description);

    if match:
        hours   = int(match.group(1));
        minutes = int(match.group(2));
        return datetime.combine(date, time(hours, minutes));

    else:
        return None;

def addEvents(page, year, cal):
    ''' adds events to the calendar '''
    soup  = BeautifulSoup(page, features="lxml")
    table = soup.find_all("div", {"id": "right-column-content"})[1]

    # loop over the list and get all list entries
    for li in table.find_all("li"):

        summ  = getSumm(li)
        descr = getDescr(li)

        event = Event()
        event.add('summary', summ)
        event.add('description', descr)

        dates = getDate(li, year)
        multidate = len(dates) > 1;

        if multidate: # sometimes a celestial event spans multiple days
            event.add('dtstart', dates[0])
            event.add('dtend', dates[-1] + timedelta(days=1))

        else:
            start = dates[0]
            time = extractTime(descr, start)

            if time:
                delta = timedelta(hours=1)
                event.add('dtstart', time - delta)
                event.add('dtend', time + delta)

            else:
                event.add('dtstart', start)

        event.add('dtstamp', datetime.now())
        event['uid'] = "".join([ str(cm) for cm in dates ]) + summ + "@seasky.org"
        cal.add_component(event)
    return cal

def main():
    # start a calendar
    cal = initCal()
    # loop over the years
    for year in range(*years):
        URL = "http://www.seasky.org/astronomy/astronomy-calendar-%s.html"%year
        print(URL)
        http = urllib3.PoolManager()
        r = http.request('GET', URL)
        page  = r.data
        cal = addEvents(page, year, cal)
    saveIcal(cal)

if __name__ == "__main__":
    main()

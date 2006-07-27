# Copyright (c) 2006-2006 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

"""date manipulation helper functions"""


def date_range(begin, end, step=1):
    """
    enumerate dates between begin and end dates.

    step can either be oneDay, oneHour, oneMinute, oneSecond, oneWeek
    use RelativeDateTime(months=1,day=-1) to enumerate months
    """
    date = begin
    while date < end :
        yield date
        date += step

# def enum_months(begin, end, day=1):
#     klass = type(begin)
#     date = begin
#     while date < end:
#         yield date
#         date = RelativeDateTime(months=+1)

FRENCH_FIXED_HOLIDAYS = {
    'jour_an'        : '%s-01-01',
    'fete_travail'   : '%s-05-01',
    'armistice1945'  : '%s-05-08',
    'fete_nat'       : '%s-07-14',
    'assomption'     : '%s-08-15',
    'toussaint'      : '%s-11-01',
    'armistice1918'  : '%s-11-11',
    'noel'           : '%s-12-25',
    }


FRENCH_MOBILE_HOLIDAYS = {
    'paques2004'    : '2004-04-12',
    'ascension2004' : '2004-05-20',
    'pentecote2004' : '2004-05-31',
    
    'paques2005'    : '2005-03-28',
    'ascension2005' : '2005-05-05',
    'pentecote2005' : '2005-05-16',
    
    'paques2006'    : '2006-04-17',
    'ascension2006' : '2006-05-25',
    'pentecote2006' : '2006-06-05',
    
    'paques2007'    : '2007-04-09',
    'ascension2007' : '2007-05-17',
    'pentecote2007' : '2007-05-28',
    }


def get_national_holidays(begin, end):
    """return french national days off between begin and end"""
    holidays = [strptime(datestr, '%Y-%m-%d')
                for datestr in FRENCH_MOBILE_HOLIDAYS.values()]
    for year in xrange(begin.year, end.year+1):
        holidays += [strptime(datestr % year, '%Y-%m-%d')
                     for datestr in FRENCH_FIXED_HOLIDAYS.values()]
    return [day for day in holidays if begin <= day < end]



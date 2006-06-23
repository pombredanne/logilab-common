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


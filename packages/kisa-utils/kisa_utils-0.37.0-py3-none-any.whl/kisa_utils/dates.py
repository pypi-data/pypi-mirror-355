import datetime
import time
from typing import Tuple

WEEK_DAYS = {
    1:'Monday', 2:'Tuesday', 3:'Wednesday',
    4:'Thursday', 5:'Friday', 6:'Saturday',
    7: 'Sunday'
}

def weekRange(date:str|datetime.datetime) -> Tuple[str,str]: # assumes standardizedDates to be given
    'return week range (monday-sunday) in thich a date(YYYY-MM-DD) belongs'
    
    if isinstance(date,(str,bytes)):
        date = datetime.datetime.strptime(date, '%Y-%m-%d')

    weekStart = (date - datetime.timedelta(days=date.weekday()-0)).strftime('%Y-%m-%d')
    weekEnd = (date +datetime.timedelta(days=6-date.weekday())).strftime('%Y-%m-%d')
    
    return weekStart,weekEnd

 # assumes standardizedDates to be given
def humanizeDate(date:str, includeWeekDay:bool=False) -> str:
    '''
    convert 'YYYY-MM-DD' to 'DD MonthCode YYYY' eg
    2021-09-23 - > '23 Sep 2021' || ''Thu 23 Sep 2021''
    '''
        
    if includeWeekDay:
        return datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%a %d %b %Y')

    return datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%d %b %Y')
    
    #date = date.split('-')
    #return f'{date[2]} {MONTH_CODES[date[1]]} {date[0]}'

def dehumanizeDate(date:str) -> str:
    if 2==date.count(' '):
        return datetime.datetime.strptime(date, '%d %b %Y').strftime('%Y-%m-%d')

    return datetime.datetime.strptime(date, '%a %d %b %Y').strftime('%Y-%m-%d')

def daysBetweenDates(dateFrom, dateTo):  # assumes standardizedDates to be given
    'dates given are in format YYYY-MM-DD'
    return (datetime.datetime.strptime(dateTo, '%Y-%m-%d') - datetime.datetime.strptime(dateFrom, '%Y-%m-%d')).days

def daysBetweenDatesInlusive(dateFrom:str, dateTo:str):  # assumes standardizedDates to be given
    days = daysBetweenDates(dateFrom, dateTo)
    return (abs(days)+1) * (-1 if days<0 else +1)

def howLongAgo(dateFrom, dateTo, shortestVersion:bool=True):
    days = daysBetweenDates(dateFrom, dateTo)

    return_str = ''
    
    if days>=365:
        years = int(days/365)
        days = days%365
        return_str += f'{years} {"years" if years>1 else "year"}'
    
    if days >=30:
        months = int(days/30)
        days = days%30
        if return_str: return_str +=', '
        return_str += f'{months} {"months" if months>1 else "month"}'

    if shortestVersion and return_str.count(',')>=1:
        return return_str

    if days >=7:
        weeks = int(days/7)
        days = days%7
        if return_str: return_str +=', '
        return_str += f'{weeks} {"weeks" if weeks>1 else "week"}'

    if shortestVersion and return_str.count(',')>=1:
        return return_str
        
    if days:
        if return_str: return_str +=', '
        return_str += f'{days} {"days" if days>1 else "day"}'
        
    return return_str

def currentTimestamp():
    '''
    get current timestamp in EAT, YYYY-MM-DD HH:MM:SS
    '''
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=3.00)
    return str(now)[:19]

def dateFrom(date,days,hours=0):
    'date: YYYY-MM-DD'
    date = datetime.datetime.strptime(date, '%Y-%m-%d')
    return str(date+datetime.timedelta(days=days, hours=hours))[:10]

def dateFromNow(days=0,hours=0):
    '''
    get current timestamp in EAT, YYYY-MM-DD HH:MM:SS
    '''
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=3.00)
    return str(now+datetime.timedelta(days=days, hours=hours))[:19]

# thanks to airtel & MTN strange date formats, we have this
def standardizedDate(date:str, fmt=''):
    'return "YYYY-MM-DD HH:MM:SS"'
    _date = None

    date = date.replace('/','-').replace('"','').replace("'",'')
    date = '-'.join([(_ if len(_)>1 else f'0{_}') for _ in date.split('-')])

    if len(date)<len('YYYY-MM-DD'): raise ValueError('invalid date given')
    if not fmt: raise ValueError('no format given')

    fmt = fmt.upper().replace('PM','AM')

    fmt = {
        'DD-MM-YYYY HH:MM:SS':'%d-%m-%Y %H:%M:%S',
        'MM-DD-YYYY HH:MM:SS':'%m-%d-%Y %H:%M:%S',
        
        'DD-MM-YYYY HH:MM:SS AM':'%d-%m-%Y %I:%M:%S %p',
        'MM-DD-YYYY HH:MM:SS AM':'%m-%d-%Y %I:%M:%S %p',

        'DD-MM-YYYY HH:MM':'%d-%m-%Y %H:%M',
        'MM-DD-YYYY HH:MM':'%m-%d-%Y %H:%M',
        
        'DD-MM-YYYY HH:MM AM':'%d-%m-%Y %I:%M %p',
        'MM-DD-YYYY HH:MM AM':'%m-%d-%Y %I:%M %p',
        
        'YYYY-MM-DD':'%Y-%m-%d',
        'DD-MM-YYYY':'%d-%m-%Y',
        'MM-DD-YYYY':'%m-%d-%Y',
        
        'YYYY-MM-DD HH:MM:SS':'%Y-%m-%d %H:%M:%S',
        'YYYY-MM-DD HH:MM:SS AM':'%Y-%m-%d %I:%M:%S %p',

        'YYYY-MM-DD HH:MM':'%Y-%m-%d %H:%M',
        'YYYY-MM-DD HH:MM AM':'%Y-%m-%d %I:%M %p',
    }.get(fmt,None)

    if not fmt: raise ValueError('unknown date format given')

    try:
        _date = datetime.datetime.strptime(date, fmt)
    except:
        raise ValueError('failed to format date to standard time')
    return str(_date)
# -----------------------------------------------------------------
def _testStandardizeTime():
    for date,fmt in [
        ('10/7/2022 19:31:30','DD-MM-YYYY HH:MM:SS'),
        ('7/10/2022 19:31:30','MM-DD-YYYY HH:MM:SS'),
        ('10/7/2022 07:31:30 pm','DD-MM-YYYY HH:MM:SS AM'),
        ('7/10/2022 07:31:30 pm','MM-DD-YYYY HH:MM:SS AM'),
        ('10/7/2022 19:31','DD-MM-YYYY HH:MM'),
        ('7/10/2022 19:31','MM-DD-YYYY HH:MM'),
        ('10/7/2022 07:31 pm','DD-MM-YYYY HH:MM AM'),
        ('7/10/2022 07:31 pm','MM-DD-YYYY HH:MM AM'),
        ('2022-7-10','YYYY-MM-DD'),
        ('10-07-2022','DD-MM-YYYY'),
        ('07-10-2022','MM-DD-YYYY'),
        ('2022-7-10 19:3:30','YYYY-MM-DD HH:MM:SS'),
        ('2022-7-10 7:31:30 pm','YYYY-MM-DD HH:MM:SS AM'),
        ('2022-7-10 19:31','YYYY-MM-DD HH:MM'),
        ('2022-7-10 7:31 pm','YYYY-MM-DD HH:MM AM'),

    ]:
        print(date,'->',standardizedDate(date,fmt))

def lastWeekOn(day:int, humanize:bool=False):
    '''
        day: 1=Monday, 7=Sunday
        get date of day in last week eg lastWeekOn(1) -> date of monday, last week
    '''
    assert isinstance(day,int) and 1<=day<=7

    now = datetime.datetime.utcnow()+datetime.timedelta(hours=+3)
    today = now.weekday() + 1

    date = now + datetime.timedelta(days=-(today-day)-7)
    strDate = f'{date}'[:10]

    if humanize:
        return humanizeDate(strDate)
    return strDate

def secondsSinceEpoch()->int:
    return int(time.time())

def minutesSinceEpoch()->int:
    return secondsSinceEpoch() // 60

def today() -> str:
    return currentTimestamp()[:10]

def tomorrow() -> str:
    return dateFromNow(days=+1)[:10]

def yesterday() -> str:
    return dateFromNow(days=-1)[:10]

def endOfMonth(year:str|int, month:str|int) -> str:
    '''
    get the last date of the given month
    @arg `year`: str|int, 4 characters representing the year
    @arg `month`: str|int, 1|2 characters representing the month
    '''

    year = f'{year}'
    month = f'{month}'

    if not(year.isdigit() and month.isdigit()) or 4!=len(year) or len(month)>2:
        raise ValueError('invalid year or month given')

    if 1==len(month): month = f'0{month}'

    if not 1<=int(month)<=12:
        raise ValueError('invalid month given')

    lastDay = f'{year}-{month}-28'
    nextDay = dateFrom(lastDay, days=+1)

    while nextDay[:7] == lastDay[:7]:
        lastDay = nextDay
        nextDay = dateFrom(lastDay, days=+1)

    return lastDay

def endOfCurrentMonth() -> str:
    '''
    get last date of the current month
    '''

    dateToday = today()

    year, month, day = dateToday.split('-')
    return endOfMonth(year, month)

def dateIsValid(date:str) -> bool:
    '''
    check if a date is valid in the format 'YYYY-MM-DD'
    @arg `date:str`: the date to check
    @return `bool`. True=date is valid, False = date is invalid
    '''
    try:
        standardizedDate(date, 'YYYY-MM-DD')
    except:
        return False
    
    return True

def isWeekend(date:str) -> bool:
    return humanizeDate(date, includeWeekDay=True).split(' ')[0] in ['Sat','Sun']

def isSunday(date:str) -> bool:
    return humanizeDate(date, includeWeekDay=True).split(' ')[0] in ['Sun']

def isSaturday(date:str) -> bool:
    return humanizeDate(date, includeWeekDay=True).split(' ')[0] in ['Sat']

if __name__=='__main__':
    print(lastWeekOn(3, humanize=True))
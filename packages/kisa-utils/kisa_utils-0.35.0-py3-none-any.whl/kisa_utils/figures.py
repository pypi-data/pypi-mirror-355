from typing import List

def humanizeFigure(figure:int|float, toInt:bool=True, useNearestUpper:bool=False) -> str:
    '''
    return string version of figure with commas where they make sense eg
    123456 -> 123,456
    '''
    #if figure<1000:
    #    return str(figure)

    figure = figure if figure else 0

    if useNearestUpper:
        toInt = True

    if toInt: 
        figure = int(figure)

    if useNearestUpper:
        figure = toNearestUpper(figure)

    figureAsString = str(figure)
    sign_prefix = ''
    if (figureAsString and '-'==figureAsString[0]):
        sign_prefix = '-'
        figureAsString = figureAsString[1:]

    decimal = '.'+figureAsString.split('.')[-1] if '.' in figureAsString else ''
    real = figureAsString.split('.')[0]
    
    real_len = len(real)

    comma_count = real_len//3 if real_len%3 else (real_len//3)-1
    
    value:List[str] = []
    
    n = 1
    while n<=real_len:
        value.insert(0,real[-n])
        if (not n%3) and (n!=real_len):
            value.insert(0,',')
        n += 1
    
    return sign_prefix + ''.join(value)+decimal

def toNearestUpper(value, base=100):
    'convert figures to nearest upper base eg 562:base100 -> 600'
    value = int(value)
    return int(value + base-(value%base) if value%base else value)

def toNearestLower(value, base=100):
    'convert figures to nearest lower base eg 532:base100 -> 500'
    value = int(value)
    return int(value - (value%base) if value%base else value)

def toNearest(value, base=100):
    if value%base < base/2: return toNearestLower(value,base)
    else: return toNearestUpper(value,base)

def splitNumber(number:int, interval:int=3):
    n = str(number)
    _n=''
    for index,xter in enumerate(n):
        _n += xter
        if index and not (index+1)%interval:
            _n += ' '
    _n = _n.strip()

    return _n

def phoneNumber(number:str, countryCode = '256') -> str|None:
    number = number.strip('+')
    if not number.isdigit(): return None

    if number.startswith(countryCode): 
        return None if len(number) not in [12] else number
    
    number = str(number).strip().lstrip('0')
    
    if number.startswith(countryCode):
        number = number[len(countryCode):]
    if number.startswith('0'):
        number = number[1:]
    
    number = countryCode + number
    
    if len(number) not in [12]:
        return None
    
    return number

def network(number:str) -> str|None:
    _standardizedNumber = phoneNumber(number)
    if not _standardizedNumber:
        return None
    
    networkCodes = _standardizedNumber[3:5]
    if networkCodes in ['77','78','76']:
        return 'mtn'
    elif networkCodes in ['70','75','74']:
        return 'airtel'
    return None

if __name__=='__main__':
    for number,status in [
        ('70',None),
        ('701173040','256701173040'),
        ('0701173040','256701173040'),
        ('+2560701173040','256701173040'),
        ('+256701173040','256701173040'),
        ('256701173040','256701173040'),
        ('25670117304',None),
    ]:
        reply = phoneNumber(number)
        assert reply==status, f'{number} returned {reply} instead of {status}'
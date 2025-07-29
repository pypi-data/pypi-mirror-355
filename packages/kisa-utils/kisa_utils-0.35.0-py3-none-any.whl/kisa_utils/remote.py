import requests

def sendRequest(url:str|bytes, method:str|bytes='post', jsonPayload:dict={}, timeout:int=180, **requestKwargs) -> dict:
    '''
    attempt to send request with JSON payload.
    @param url: resource to send request to
    @param method: request method; one of GET|POST
    @param jsonPayload: dictionary with payload data
    @param timeout: how long to wait[SECONDS] before raising the timeout error

    @return {'status':BOOL, 'log':STR, 'responseType':STR|JSON, 'response':None|STR|DICT}
    '''

    reply = {'status':False, 'log':'', 'response':None}

    method = method.lower()
    if method not in ['get','post']:
        reply['log'] = 'invalid method given'
        return reply

    try:
        if 'get'==method:
            response = requests.get(url,json=jsonPayload,timeout=(5,timeout), **requestKwargs)
        elif 'post'==method:
            response = requests.post(url,json=jsonPayload,timeout=(5,timeout), **requestKwargs)
        else:
            reply['log'] = 'invalid method given'
            return reply

        if response.status_code!=200:
            reply['log'] = f'response returned error code: {response.status_code}, `{response.reason}`'
            return reply

        try:
            responseJSON = response.json()
            reply['response'] = responseJSON
            reply['status'] = True
            return reply
        except:
            reply['log'] = 'no JSON reply got'
            return reply
            
    except requests.exceptions.Timeout:
        reply['log'] = 'connection timeout'
        return reply
    except requests.exceptions.ConnectionError:
        reply['log'] = 'connection failed'
        return reply


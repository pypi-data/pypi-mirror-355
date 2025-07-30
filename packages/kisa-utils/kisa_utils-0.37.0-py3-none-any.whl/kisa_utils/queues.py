'''
this module is reponsible to creating and managing named queues for KISA

@author bukman, <glayn2bukman@gmail.com>, (256)701-173-049
'''

from queue import Queue as pyQueue
from .structures import validator as structureValidator
from . import threads

class QueueException(Exception):
    pass

class Queue:
    __ACTIVE_QUEUES = {}

    def __init__(self, name:str, executor:callable, inputDefinitions:dict={}):
        '''
        create a new queue object

        @param `name`: the name of the queue
        @param `executor`: the function/callback to call when data is available in the queue
        @param `inputDefinitions`: {
            'args': tuple[type], # a tuple with each arg's type given 
            'kwargs': { str : type, ...}, # each kwarg's type is given
        }
        '''
        activeQueues = self.__ACTIVE_QUEUES

        inputDefinitions['args'] = inputDefinitions.get('args',())
        inputDefinitions['kwargs'] = inputDefinitions.get('kwargs',{})

        if name in activeQueues:
            raise QueueException(f'a queue already named `{name}` exists')

        if not callable(executor):
            raise QueueException('given `executor` is not a function/callable')

        executorName = executor.__name__
        if executorName.startswith('<'):
            raise QueueException('lambda functions are not allowed')

        if not (
            isinstance(inputDefinitions, dict) and \
            ('args' in inputDefinitions) and isinstance(inputDefinitions['args'],(tuple,list)) and\
            ('kwargs' in inputDefinitions) and isinstance(inputDefinitions['kwargs'],dict) \
        ):
            raise QueueException('invalid `inputDefinitions` given')

        for kwarg in inputDefinitions['kwargs']:
            if not isinstance(kwarg,str):
                raise QueueException('all keys in inputDefinitions->kwargs must be strings')

        self.executor = executor
        self.inputDefinitions = inputDefinitions
        self.pyQueue = pyQueue()
        
        activeQueues[name] = self

        print(threads.runEvery(self.reader, 0.001))

    def reader(self):
        while 1:
            while not self.pyQueue.empty():
                data = self.pyQueue.get()
                self.executor(*data['args'], **data['kwargs'])

    def push(self, *args, **kwargs) -> dict:
        '''
        push `args` and `kwargs` to the queue so that the executor can act on them when the time comes
        '''
        reply = {'status':False, 'log':''}

        argsValidatorReply = structureValidator.validate(args, self.inputDefinitions['args'])
        if not argsValidatorReply['status']: return argsValidatorReply

        kwargsValidatorReply = structureValidator.validate(kwargs, self.inputDefinitions['kwargs'])
        if not kwargsValidatorReply['status']: return kwargsValidatorReply

        self.pyQueue.put({
            'args':args,
            'kwargs':kwargs
        })

        reply['status'] = True
        return reply

def nameIsRegistered(name:str) -> bool:
    '''
    check if a queue with called `name` exists

    @param `name`: the queue name
    '''
    return name in Queue._Queue__ACTIVE_QUEUES

def create(name:str, executor:callable, inputDefinitions:dict={}) -> dict:
    '''
    create a new queue object

    @param `name`: the name of the queue
    @param `executor`: the function/callback to call when data is available in the queue
    @param `inputDefinitions`: {
        'args': tuple[type], # a tuple with each arg's type given 
        'kwargs': { str : type, ...}, # each kwarg's type is given
    }

    @returns {'status':BOOL, 'log':STR, 'queue':QUEUE_OBJECT}
    '''

    reply = {'status':False, 'log':'', 'queue':None}

    inputDefinitions['kwargs'] = inputDefinitions.get('kwargs',None) or {}

    if nameIsRegistered(name):
        if inputDefinitions!=Queue._Queue__ACTIVE_QUEUES[name].inputDefinitions:
            reply['log'] = f'a queue with the name `{name}` already exisits and has different inputDefinitions'
        else:
            reply['status'] = True
            reply['queue'] = Queue._Queue__ACTIVE_QUEUES[name]

        return reply
    
    try:
        queue = Queue(name, executor, inputDefinitions)
    except Exception as e:
        reply['log'] = f'{e}'
        return reply
    
    reply['status'] = True
    reply['queue'] = queue
    return reply

def push(name:str, *args, **kwargs) -> dict:
    '''
    push `args` and `kwargs` to the queue so that the executor can act on them when the time comes

    @param `name`: name of the queue
    '''
    reply = {'status':False, 'log':''}

    queue = Queue._Queue__ACTIVE_QUEUES.get(name,None)

    if not queue:
        reply['log'] = f'could not find queue named `{name}`'
        return reply

    return queue.push(*args, **kwargs)

def get(name:str) -> Queue | None:
    return Queue._Queue__ACTIVE_QUEUES.get(name,None)

if __name__=='__main__':
    def addNumbers(a:int,b:int):
        print(f'{a}+{b}={a+b}')

    queueReply = create('testQueue',addNumbers,{'args':(int,int)})
    print(queueReply)
    # queue = queueReply['queue']
    queue:Queue = get('testQueue')

    for i in range(15):
        print(queue.push(i,10))
        print(push('testQueue',i,'k'))
        # threads.runOnce(push, 'testQueue', i, 10)
        # threads.runOnce(push, 'testQueue', 10, i)
        # threads.runOnce(queue.push,f'count-obj: {i}')



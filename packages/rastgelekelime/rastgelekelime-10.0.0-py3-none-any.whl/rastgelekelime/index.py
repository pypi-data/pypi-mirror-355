import random
import json
import os

with open(os.path.join(os.path.dirname(__file__), 'data', 'wordList.json'), 'r', encoding='utf-8') as f:
    wordList = json.load(f)

def words(options=None):
    def word():
        if options and 'maxLength' in options and options['maxLength'] > 1:
            return generateWordWithMaxLength()
        else:
            return generateRandomWord()

    def generateWordWithMaxLength():
        while True:
            wordUsed = generateRandomWord()
            if len(wordUsed) <= options['maxLength']:
                return wordUsed

    def generateRandomWord():
        return random.choice(wordList)

    if options is None:
        return word()

    if isinstance(options, int):
        options = {'exactly': options}

    if 'exactly' in options:
        options['min'] = options['exactly']
        options['max'] = options['exactly']

    if 'wordsPerString' not in options or not isinstance(options['wordsPerString'], int):
        options['wordsPerString'] = 1

    if 'formatter' not in options or not callable(options['formatter']):
        options['formatter'] = lambda word, _: word

    if 'separator' not in options or not isinstance(options['separator'], str):
        options['separator'] = ' '

    total = options['min'] + random.randint(0, options['max'] - options['min'])
    results = []
    token = ''
    relativeIndex = 0

    for i in range(total * options['wordsPerString']):
        if relativeIndex == options['wordsPerString'] - 1:
            token += options['formatter'](word(), relativeIndex)
        else:
            token += options['formatter'](word(), relativeIndex) + options['separator']
        relativeIndex += 1
        if (i + 1) % options['wordsPerString'] == 0:
            results.append(token)
            token = ''
            relativeIndex = 0

    if 'join' in options and isinstance(options['join'], str):
        results = options['join'].join(results)

    return results

__all__ = ['words', 'wordList'] 
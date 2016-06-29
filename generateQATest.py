import sys
import getopt
from enum import Enum
import json
import re
import bisect
import spacy
import string
import random
import io

# Source of invalid options, whether it is from same passage or random passage
CORPUS_TYPE = Enum('CORPUS_TYPE', 'SAME_PASSAGE RANDOM_PASSAGE')
CORPUS_TYPE = 'RANDOM_PASSAGE'
# Number of invalid options
VARIATION_COUNT = 4
# For corpus type of SAME_PASSAGE, if the passage is smaller then
# variation count, whether to skip it
SKIP_SMALL_PASSAGE = False
# Whether we allow duplicate or not in the choices
ALLOW_DUPLICATE_ANSWER = False
# Duplicate for small passage
ALLOW_DUPLICATE_FOR_SMALL = True
# Allow combination of contexts to generate enough length for the passage
ENABLE_CONTEXT_COMBINATION = True
# If context combination, specify the minimum sentence length
MINIMUM_CONTEXT_LENGTH = VARIATION_COUNT + 1
# Whether to remove the right sentence from the context,
# preventing network to learn by looking at duplicate in RANDOM_PASSAGE mode
IS_RIGHT_SENTENCE_REMOVED = True
# Boolean for printing meta file
IS_META_PRINT = True
# QA separator
QA_SEPARATOR = "*" * 50
# Use Spacy NLP
IS_SPACY = True
NLP = spacy.load('en')
# Allow some characters to be removed/added by spacy
SPACY_TOLERANCE = 10
# Answer choices
ANSWER_CHOICES = string.uppercase
# log error
LOG_ERROR = True
LOG_FILE = open('log.err', 'w')
# log debug
LOG_DEBUG = True
DEBUG_FILE = open('debug.err', 'w')
# progress loop counter
PROGRESS_LOOP = 10

NON_ALPHANUMERIC_REGEX = "[^a-zA-Z\d]"

def logError(text):
    LOG_FILE.write(repr(text) + '\n')

def logDebug(text):
    DEBUG_FILE.write(repr(text) + '\n')

def handleInputError():
    print 'Error! Correct format: python generateQATest.py -i <inputFile> -o <outputFile>'
    sys.exit(2)

def handleWarning():
    logError("Skipping this context")

def handleToleranceError():
    pass
    # assert False

def printMeta(inputFile, outputFile, inputJson):
    version = inputJson['version']
    print "Input file name is: ", inputFile
    print "Output file name is: ", outputFile
    print "Version of input data: ", version

def generateSolutions(context, rightSentence):
    answers = []
    sentences = getSentenceList(context)
    isPassageSmall = len(sentences) < VARIATION_COUNT + 1
    if SKIP_SMALL_PASSAGE and isPassageSmall:
        logError("Warning, not enough sentences for same passage options")
        return None

    correctChoice = ANSWER_CHOICES[random.randint(0, VARIATION_COUNT)]
    sentences.remove(rightSentence)
    if len(sentences) == 0:
        return None
    for choice in ANSWER_CHOICES[0:VARIATION_COUNT + 1]:
        if choice == correctChoice:
            answers.extend(["*", choice, ')', rightSentence, '\n'])
        else:
            wrongIdx = random.randint(0, len(sentences) - 1)
            wrongSentence = sentences[wrongIdx]
            answers.extend([choice, ')', wrongSentence, '\n'])
            if ALLOW_DUPLICATE_FOR_SMALL and isPassageSmall:
                continue
            elif not ALLOW_DUPLICATE_ANSWER:
                sentences.remove(wrongSentence)
    return ''.join(answers)

def getRandomExcept(start, end, idx):
    randIdx = idx
    while randIdx == idx:
        randIdx = random.randint(start, end)
    return randIdx

def generateRPSolutions(inputJson, currentIdx,
                        rightSentence, count=VARIATION_COUNT):
    answers = []
    topics = inputJson['data']
    correctChoice = ANSWER_CHOICES[random.randint(0, VARIATION_COUNT)]
    for choice in ANSWER_CHOICES[0:VARIATION_COUNT + 1]:
        if choice == correctChoice:
            answers.extend(["*", choice, ')', rightSentence, '\n'])
        else:
            randomParagraphs = topics[getRandomExcept(0,
                                      len(topics) - 1, currentIdx)]['paragraphs']
            randomContext = randomParagraphs[random.randint(0, len(randomParagraphs) - 1)]['context']
            if IS_SPACY:
                randomContext = parseBySpacy(randomContext)
            sentences = getSentenceList(randomContext)
            wrongIdx = random.randint(0, len(sentences) - 1)
            wrongSentence = sentences[wrongIdx]
            answers.extend([choice, ')', wrongSentence, '\n'])
    return ''.join(answers)

def parseBySpacy(context):
    doc = NLP(context, parse=True)
    document = []
    for sent in doc.sents:
        sentence = re.sub('\.', '_', sent.string.strip())
        if sentence[-1] == '_':
            sentence = sentence[:-1] + '.'
        if sentence[-1] != '.':
            sentence += '.'
        document.append(sentence)
    document = ' '.join(document)
    if len(context) != len(document):
        if abs(len(context) - len(document)) > SPACY_TOLERANCE:
            message = ("Error of Spacy {} is larger than allowed tolerance".
                       format(abs(len(context) - len(document))))
            print message
            logError("****" + message)
            # logError(document)
            handleToleranceError()
        elif abs(len(context) - len(document)) <= SPACY_TOLERANCE:
            # logError("len of spacy parsed sentences is differed by {}.".
            #          format(abs(len(context) - len(document))))
            pass
    return document

def findSentence(context, index):
    sentences = re.split('[.!?]', context)
    accuLengthList = [0]
    for sentence in sentences:
        accuLengthList.append(len(sentence) + accuLengthList[-1] + 1)
    rightSentence = sentences[bisect.bisect(accuLengthList, index) - 1]
    return rightSentence.lower().strip()



def getCQAList(document):
    contextList = []
    questionList = []
    rightSentenceList = []
    for paragraph in document['paragraphs']:
        originalContext = paragraph['context']
        if IS_SPACY:
            context = parseBySpacy(originalContext)
        else:
            context = originalContext
        context = context.lower()
        contextList.append(context)

        qaList = paragraph['qas']
        questions = []
        rightAnswers = []
        for qa in qaList:
            answerMidIdx = qa['answers'][0]['answer_start'] + \
                            len(qa['answers'][0]['text']) / 2
            rightSentence = findSentence(context,
                                         answerMidIdx)
            rightSentenceString = ' '.join(re.split(NON_ALPHANUMERIC_REGEX,
                                           rightSentence.lower()))
            answerString = ' '.join(re.split(NON_ALPHANUMERIC_REGEX,
                                    qa['answers'][0]['text'].lower())).strip()
            if answerString not in rightSentenceString:
                logError("*****Mismatch answer and sentence in >>>{}<<< *****".
                         format(repr(document['title'])))
                logError(repr(rightSentenceString))
                logError(repr(answerString))
            questions.append(qa['question'])
            rightAnswers.append(rightSentence)
        questionList.append(questions)
        rightSentenceList.append(rightAnswers)

    return contextList, questionList, rightSentenceList

def removeSentenceFromContext(context, rightSentence):
    sentences = getSentenceList(context)
    sentences.remove(rightSentence)
    sentences.append('')
    context = '. '.join(sentences).strip()
    return context

def getSentenceList(context):
    sentences = re.split('[.!?]', context)
    sentences = [sentence.strip().lower()
                 for sentence in sentences if len(sentence) > 0]
    return sentences

def _getCombinedContext(contextList, j):
    context = contextList[j]
    sentences = getSentenceList(context)
    k1 = j
    k2 = j
    bfRandom = random.randint(0,1)
    while len(sentences) <= MINIMUM_CONTEXT_LENGTH:
        if bfRandom == 1:
            if k1 < len(contextList) - 1:
                additionalSentences = getSentenceList(contextList[k1 + 1])
                sentences.extend(additionalSentences)
                k1 += 1
            elif k2 > 0:
                additionalSentences = getSentenceList(contextList[k2 - 1])
                additionalSentences.extend(sentences)
                sentences = additionalSentences
                k2 -= 1
            else:
                logError('***********Topic is too small!**********')
                assert False
        else:
            if k2 > 0:
                additionalSentences = getSentenceList(contextList[k2 - 1])
                additionalSentences.extend(sentences)
                sentences = additionalSentences
                k2 -= 1
            elif k1 < len(contextList) - 1:
                additionalSentences = getSentenceList(contextList[k1 + 1])
                sentences.extend(additionalSentences)
                k1 += 1
            else:
                logError('***********Topic is too small!**********')
                assert False
    sentences.append('')
    context = '. '.join(sentences).strip()
    return context

def generateQA(inputFile, outputFile):
    inputJson = json.load(open(inputFile, 'r'))
    if IS_META_PRINT:
        printMeta(inputFile, outputFile, inputJson)
    topics = inputJson['data']
    totalCount = len(topics)
    questionCount = 0
    for i, document in enumerate(topics):
        contextList, questionList, rightSentenceList = getCQAList(document)
        for j in range(len(contextList)):
            if ENABLE_CONTEXT_COMBINATION:
                context = _getCombinedContext(contextList, j)
            else:
                context = contextList[j]

            for question, rightSentence \
                    in zip(questionList[j], rightSentenceList[j]):
                if IS_RIGHT_SENTENCE_REMOVED:
                    contextProcessed = removeSentenceFromContext(context,
                                                                 rightSentence)
                else:
                    contextProcessed = context
                if CORPUS_TYPE == 'SAME_PASSAGE':
                    answers = generateSolutions(context, rightSentence)
                elif CORPUS_TYPE == 'RANDOM_PASSAGE':
                    answers = generateRPSolutions(inputJson,
                                                  i, rightSentence)
                if contextProcessed is not None and answers is not None:
                    questionCount += 1
                    yield QA_SEPARATOR + '\n' + contextProcessed + '\n' + \
                        str(questionCount) + '. ' + question + '\n' + answers

        if i % PROGRESS_LOOP == 0:
            print "{0}/{1}".format(i, totalCount)



def main(argv):
    # load user input argument
    inputFile = ''
    outputFile = ''

    if not argv:
        handleInputError()
    try:
        opts, args = getopt.getopt(argv, "hi:o:", ['ifile=', '-ofile='])
    except getopt.GetoptError:
        handleInputError()
    for opt, arg in opts:
        if opt == '-h':
            handleInputError()
        elif opt == "-i":
            inputFile = arg
        elif opt == "-o":
            outputFile = arg
        else:
            handleInputError()
    # generate the QA Test
    with io.open(outputFile, 'w', encoding = 'utf-8') as f:
        for qa in generateQA(inputFile, outputFile):
            f.write(qa)
            f.write(unicode('\n', encoding='utf8'))


if __name__ == "__main__":
    main(sys.argv[1:])
    LOG_FILE.close()
    DEBUG_FILE.close()
    print "Done."

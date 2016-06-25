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
# TODO: RANDOM_PASSAGE implementation
# Number of invalid options
VARIATION_COUNT = 1
# For corpus type of SAME_PASSAGE, if the passage is smaller then
# variation count, whether to skip it
SKIP_SMALL_PASSAGE = True
# Whether we allow duplicate or not in the choices 
ALLOW_DUPLICATE_ANSWER = False
# Duplicate for small passage
ALLOW_DUPLICATE_FOR_SMALL = True
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
# progress loop counter
PROGRESS_LOOP = 25

NON_ALPHANUMERIC_REGEX = "[^a-zA-Z\d]"

def logError(text):
    LOG_FILE.write(repr(text) + '\n')

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
    sentences = re.split('[.!?]', context)
    sentences = [sentence.strip().lower()
                 for sentence in sentences if len(sentence) > 0]
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

def generateQA(inputFile, outputFile):
    inputJson = json.load(open(inputFile, 'r'))
    if IS_META_PRINT:
        printMeta(inputFile, outputFile, inputJson)
    totalCount = len(inputJson['data'])
    for i, document in enumerate(inputJson['data']):
        title = document['title']
        for paragraph in document['paragraphs']:
            originalContext = paragraph['context']
            if IS_SPACY:
                context = parseBySpacy(originalContext)
            else:
                context = originalContext
            context = context.lower()
            qaList = paragraph['qas']
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
                    logError("*****Mismatch of answer and sentence in >>>{}<<< *****".
                             format(repr(title)))
                    logError(repr(rightSentenceString))
                    logError(repr(answerString))
                answers = generateSolutions(context, rightSentence)
                question = qa['question']
                if context is not None and answers is not None:
                    yield QA_SEPARATOR + '\n' + context + '\n' + \
                        question + '\n' + answers
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
    print "Done."

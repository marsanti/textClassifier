from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from logger import log
import os
import re
import json
import time
import math

# nltk stuff
stoplist = stopwords.words('english')
lemmatizer = WordNetLemmatizer()
ps = PorterStemmer()

# path to articles
PATH_MEDICAL_ARTICLES = 'data/train/medicalArticles'
PATH_OTHER_ARTICLES = 'data/train/otherArticles'
# use lemmatizer or stemming 
USE_LEMMATIZER = True

# util function
def readFile(filepath: str) -> str:
    text = ''
    with open(filepath, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        # clear the text 
        for line in lines:
            text += line.strip() + '\n'

    return text

def removeNonAlphanumeric(article: str) -> str:
    # whenever a non alphanumeric character is found, replace it with a space
    # exception: apostrophes and spaces
    return re.sub(r'[^a-zA-Z0-9\s\']', ' ', article)

# perform the stopwords elimination
def deleteStopwords(article: str) -> str:
    return [word.lower() for word in article if word.lower() not in stoplist]

# perform the tokenization
def performTokenization(text: str) -> list:
    return word_tokenize(text)

# perform the Porter Stemming algorithm
def performStemming(text: list) -> list:
    return [ps.stem(word) for word in text]

# perform the lemmatization of the article
def lemmatizeArticle(article: list) -> list:
    return [lemmatizer.lemmatize(word) for word in article]

# count occurrences (if article is a set then it's document occurrence else it's corpora occurrence)
def countOccurrences(occurrencesDict: dict, article: list) -> None:
    for word in article:
        if word in occurrencesDict:
            occurrencesDict[word] += 1
        else:
            occurrencesDict[word] = 1

# calculate the frequencies:
# P(Wₖ| Cⱼ) = (nₖ + α) / (n + α |vocabulary|) 
def calculateFrequencies(occurrencesDict: dict, alpha=1.0) -> dict:
    frequenciesDict = {}
    # sum all occurrences
    totalOccurrences = sum(occurrencesDict.values())
    totalwords = len(occurrencesDict)
    for (word, occurrence) in occurrencesDict.items():
        # frequenciesDict[word] = occurrence / totalOccurrences
        frequenciesDict[word] = math.log((occurrence + alpha)/(totalOccurrences + alpha * totalwords)) 
    
    return frequenciesDict

# in order to have all positive numbers:
# I add to the frequency the abs value of the min value and the max value in the frequency.
# In that way I have only positive numbers and i preserve the importance of the word.
# e.g. {min = -12, max = -4} -- after sum the calculated value --> {min = 4, max = 12}
def transformFrequenciesIntoPositiveValues(frequencyDict: dict) -> dict:
    # assuming frequencyDict is sorted
    test = abs(min(frequencyDict.values())) + abs(max(frequencyDict.values()))
    for (word, occurrence) in frequencyDict.items():
        frequencyDict[word] += test
    return frequencyDict

def performPreProcessing(article: str) -> list:
    article = removeNonAlphanumeric(article)
    # tokenize article
    text = performTokenization(article)
    # perform the stopwords elimination
    text = deleteStopwords(text)
    
    if(USE_LEMMATIZER):
        # perform lemmatization
        text = lemmatizeArticle(text)
    else:
        # perform stemming
        text = performStemming(text)


    return text

# create the Bag of Words based on document occurrences
def createBoW(isMedical: bool) -> None:
    # different path if isMedical or not
    if isMedical:
        pathToArticles = PATH_MEDICAL_ARTICLES
        jsonName = 'data/medicalOccurrences.json'
        frequenciesFile = 'data/medicalFrequencies.json'
    else:
        pathToArticles = PATH_OTHER_ARTICLES
        jsonName = 'data/otherOccurrences.json'
        frequenciesFile = 'data/otherFrequencies.json'

    # get files in the article folder
    articlesDirectory = os.listdir(pathToArticles)
    occurrencesDict = {}
    log(f'{len(articlesDirectory)} articles found in {pathToArticles}')
    # for each file read the article
    for filename in articlesDirectory:
        filepath =  pathToArticles + '/' + filename
        text = readFile(filepath)
        # process the text
        text = performPreProcessing(text)
        # count occurrences in all corpora
        countOccurrences(occurrencesDict, text)

    # sort the dict in order to have word with high occurrence at top
    occurrencesDict = dict(sorted(occurrencesDict.items(), key=lambda item: item[1], reverse=True))
    
    # save dict in a json file
    with open(jsonName, 'w', encoding='utf-8') as jsonFile:
        json.dump(occurrencesDict, jsonFile, indent=2)

    frequenciesDict = calculateFrequencies(occurrencesDict=occurrencesDict)
    frequenciesDict = transformFrequenciesIntoPositiveValues(frequenciesDict)
    frequenciesDict = dict(sorted(frequenciesDict.items(), key=lambda item: item[1], reverse=True))

    # save frequencies in a json file
    with open(frequenciesFile, 'w', encoding='utf-8') as jsonFile:
        json.dump(frequenciesDict, jsonFile, indent=2)

# main function
def main():
    log('Start creating BoWs...\n')
    startTime = time.time()
    createBoW(isMedical=True)
    createBoW(isMedical=False)
    log(f'\nFinished in {round(time.time() - startTime, 2)}s.')

if __name__ == '__main__':
    main()
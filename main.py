import argparse
import urllib
import json
import os
import oauth2
import re
import nltk
import csv
import pickle

"""file2 = open('C:/Users/xRohitGupta/Desktop/training_set.txt','r+')"""
class TwitterData:
    def parse_config(self):
        config = {}
        # from file args
        if os.path.exists('/home/pi/Desktop/mood_visualisation/config.json'):
                with open('/home/pi/Desktop/mood_visualisation/config.json') as f:
                    config.update(json.load(f))
        else:
            # may be from command line
            parser = argparse.ArgumentParser()

            parser.add_argument('-ck', '--consumer_key', default=None, help='Your developper `Consumer Key`')
            parser.add_argument('-cs', '--consumer_secret', default=None, help='Your developper `Consumer Secret`')
            parser.add_argument('-at', '--access_token', default=None, help='A client `Access Token`')
            parser.add_argument('-ats', '--access_token_secret', default=None, help='A client `Access Token Secret`')

            args_ = parser.parse_args()
            def val(key):
                return config.get(key)\
                    or getattr(args_, key)\
                    or raw_input('Your developper `%s`: ' % key)
            config.update({
                'consumer_key': val('consumer_key'),
                'consumer_secret': val('consumer_secret'),
                'access_token': val('access_token'),
                'access_token_secret': val('access_token_secret'),
            })
        # should have something now
        return config
    #end

    def oauth_req(self, url, http_method="GET", post_body=None,
                  http_headers=None):
        config = self.parse_config()
        consumer = oauth2.Consumer(key=config.get('consumer_key'), secret=config.get('consumer_secret'))
        token = oauth2.Token(key=config.get('access_token'), secret=config.get('access_token_secret'))
        client = oauth2.Client(consumer, token)

        resp, content = client.request(
            url,
            method=http_method,
            body=post_body or '',
            headers=http_headers
        )
        return content
    #end

    #start getTwitterData
    def getData(self, keyword, maxTweets):
        
        url = 'https://api.twitter.com/1.1/search/tweets.json?'
        data = {'q': keyword, 'lang': 'en', 'result_type': 'recent', 'count': maxTweets, 'include_entities': 0}

        #Add if additional params are passed
        #if params:
        #    for key, value in params.iteritems():
        #        data[key] = value

        url += urllib.urlencode(data)

        response = self.oauth_req(url)
        jsonData = json.loads(response)
        tweets = []
        if 'errors' in jsonData:
            print "API Error"
            print jsonData['errors']
        else:
            for item in jsonData['statuses']:
                tweets.append((item['text']))
                
        return tweets

#tweets = TwitterData()
#keyword = str(raw_input("Enter the keyword/keywords : "))
#maxTweets = int(raw_input('Enter No of Tweets : '))
#list1 = tweets.getData(keyword,maxTweets)
#for i in list1:
#    print i
 #   print ''

def processTweet(tweet):
    # process the tweets

    #Convert to lower case
    tweet = tweet.lower()
    #Convert www.* or https?://* to URL
    tweet = re.sub('((www\.[^\s]+)|(https?://[^\s]+))','URL',tweet)
    #Convert @username to AT_USER
    tweet = re.sub('@[^\s]+','AT_USER',tweet)
    #Remove additional white spaces
    tweet = re.sub('[\s]+', ' ', tweet)
    #Replace #word with word
    tweet = re.sub(r'#([^\s]+)', r'\1', tweet)
    #trim
    tweet = tweet.strip('\'"')
    return tweet



#start replaceTwoOrMore
def replaceTwoOrMore(s):
    #look for 2 or more repetitions of character and replace with the character itself
    pattern = re.compile(r"(.)\1{1,}", re.DOTALL)
    return pattern.sub(r"\1\1", s)
#end

#start getStopWordList
def getStopWordList(stopWordListFileName):
    #read the stopwords file and build a list
    stopWords = []
    stopWords.append('AT_USER')
    stopWords.append('URL')
    stopWords.append('rt')
    fp = open(stopWordListFileName, 'r')
    line = fp.readline()
    while line:
        word = line.strip()
        stopWords.append(word)
        line = fp.readline()
    fp.close()
    return stopWords
#end

#start getfeatureVector
def getFeatureVector(tweet):
    featureVector = []
    #split tweet into words
    words = tweet.split()
    for w in words:
        #replace two or more with two occurrences
        w = replaceTwoOrMore(w)
        #strip punctuation
        w = w.strip('\'"?,.')
        #check if the word stats with an alphabet
        val = re.search(r"^[a-zA-Z][a-zA-Z0-9]*$", w)
        #ignore if it is a stop word
        if(w in stopWords or val is None):
            continue
        else:
            featureVector.append(str(w.lower()))
    return featureVector
#end

def extract_features(tweet):
    tweet_words = set(tweet)
    features = {}
    for word in featureList:
        features['contains(%s)' % word] = (word in tweet_words)
    return features
    
#Read the tweets one by one and process it
#fp = open('/home/pi/Desktop/twitter-sentiment-analyzer-master/data/sampleTweet.txt'r')
#line = fp.readline()

inpTweets = csv.reader(open('/home/pi/Desktop/twitter-sentiment-analyzer-master/data/full_training_dataset.csv', 'rb'), delimiter=',')
#stopWords = getStopWordList('/home/pi/Desktop/twitter-sentiment-analyzer-master/data/feature_list/stopwords.txt')
featureList = []

st = open('/home/pi/Desktop/twitter-sentiment-analyzer-master/data/feature_list/stopwords.txt', 'r')
stopWords = getStopWordList('/home/pi/Desktop/twitter-sentiment-analyzer-master/data/feature_list/stopwords.txt')

#for item in list1:
#    processedTweet = processTweet(item)
#    featureVector = getFeatureVector(processedTweet)
#    print featureVector
    #line = fp.readline()

tweets = []
for row in inpTweets:
    sentiment = row[0]
    tweet = row[1]
    processedTweet = processTweet(tweet)
    featureVector = getFeatureVector(processedTweet)
    featureList.extend(featureVector)
    tweets.append((featureVector, sentiment));
#end loop
#fp.close()

featureList = list(set(featureList))

training_set = nltk.classify.util.apply_features(extract_features, tweets)
#print training_set,type(training_set)

#file2 = open('/home/pi/Desktop/mood_visualisation/my_classifier1.pickle','wb')
# Train the classifier
#NBClassifier = nltk.NaiveBayesClassifier.train(training_set)
#pickle.dump(NBClassifier, file2)
#file2.close()

file2 = open('/home/pi/Desktop/mood_visualisation/my_classifier1.pickle')
NBClassifier = pickle.load(file2)
file2.close()

 #Test the classifier
#testTweet = str(raw_input('Enter the sentence:'))
#while(testTweet != '0'):
#    processedTestTweet = processTweet(testTweet)
#    print NBClassifier.classify(extract_features(getFeatureVector(processedTestTweet)))
#    testTweet = str(raw_input('Enter the sentence:'))

"""
tweets = TwitterData()
keyword = str(raw_input("Enter the keyword/keywords : "))
maxTweets = int(raw_input('Enter No of Tweets : '))
list1 = tweets.getData(keyword,maxTweets)
for i in list1:
    print '\n'
    print i
"""

alpha = 'y'
while alpha != 'n':
    count = 1
    emotion_rating = 0.0
    tweets = TwitterData()
    keyword = str(raw_input("Enter the keyword/keywords : "))
    maxTweets = int(raw_input('Enter No of Tweets : '))
    list1 = tweets.getData(keyword,maxTweets)

    for i in list1:
        
        count += 1
        processedTestTweet = processTweet(i)
        emotion = NBClassifier.classify(extract_features(getFeatureVector(processedTestTweet)))
        print emotion
        if emotion == 'positive':
            emotion_rating += 1
        elif emotion == 'negative':
            emotion_rating -= 1
        #print emotion_rating/count*5
         
    final_rating = emotion_rating/count*5
    print final_rating
    if final_rating <= -2.0 and final_rating >= -5.0:
        rating = 1
        print rating
    elif final_rating <= -0.5 and final_rating >= -2.0:
        rating = 2
        print rating
    elif final_rating <= 0.5 and final_rating >= -0.5:
        rating = 3
        print rating
    elif final_rating <= 2.0 and final_rating >= 0.5:
        rating = 4
        print rating
    elif final_rating <= 5.0 and final_rating >= 2.0:
        rating = 5
        print rating
    
    
    alpha = str(raw_input('Do you want to continue? [y/n] : '))
#Output
#======
#positive                                                                                                                                                    

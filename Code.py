import pickle
import math
from math import log
import nltk
import re
import time
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from SPARQLWrapper import SPARQLWrapper, JSON

def snakecase(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1\2', s1).lower()
    s3 = ""
    if len(s2)>0:
    	s3 = str(chr(ord(s2[0])-32)) + s2[1:]
    return s3


wordGivenTag = {}
tagGivenTag = {}
countOfTags = {}


def PickleToDictionaries():

	global wordGivenTag,tagGivenTag,countOfTags
	with open('probWordGivenTag', 'rb') as file1:
		wordGivenTag = pickle.load(file1)
	
	with open('probTagGivenTag', 'rb') as file2:
		tagGivenTag = pickle.load(file2)
	
	with open('countOfTags', 'rb') as file3:
		countOfTags = pickle.load(file3)


def SmoothedWordGivenTag(key):

	if key not in wordGivenTag:
		return .2/float(len(wordGivenTag))
	else:
		return wordGivenTag[key]	




def testing(sentence):

	global wordGivenTag,tagGivenTag,countOfTags
	# print wordGivenTag
	# print tagGivenTag
	# print countOfTags
	B_S = dict()
	B_E = dict()
	tupl = tuple([0,"start"])
	B_S[tupl] = 0
	B_E[tupl] = None
	posTags = countOfTags.keys()
	sentence = sentence.split()
	length = len(sentence)
	for i in range(length):
		for p in posTags:
			for n in posTags:
				numToTag = tuple([i,p])
				TagToTag = tuple([p,n])	
				if numToTag in B_S and TagToTag in tagGivenTag:
					scr = B_S[numToTag]-math.log(tagGivenTag[TagToTag])-math.log(SmoothedWordGivenTag(tuple([sentence[i],n])))
					nextNumToTag = tuple([i+1,n])
					#print nextNumToTag
					if nextNumToTag not in B_S or B_S[nextNumToTag] >  scr:
						B_S[nextNumToTag] = scr
						B_E[nextNumToTag] = numToTag

	for p in posTags:
		numToTag = tuple([length,p])
		n = "stop"	
		TagToTag = tuple([p,n])
		if numToTag in B_S and TagToTag in tagGivenTag:
			scr = B_S[numToTag]-math.log(tagGivenTag[TagToTag])-math.log(SmoothedWordGivenTag(tuple([sentence[i],n])))
			nextNumToTag = tuple([length+1,n])
			if nextNumToTag not in B_S or B_S[nextNumToTag] > scr:
				B_S[nextNumToTag] = scr
				B_E[nextNumToTag] = numToTag

	
	#print B_E

	


	FinallistOfTags	= list()
	N_E = B_E[tuple([length+1,"stop"])]
	while N_E != tuple([0,"start"]):
		FinallistOfTags.append(N_E[1])
		N_E = B_E[N_E]

	FinallistOfTags.reverse()


	wordWithTags = list()
	for i in range(length):
		wordWithTags.append(tuple([sentence[i],FinallistOfTags[i]]))

	return wordWithTags	


if __name__ == '__main__':
	PickleToDictionaries()

	#DBPEDIA LINKING ================================================================================================================

	sparql = SPARQLWrapper("http://dbpedia.org/sparql")

	#TRAINING =======================================================================================================================

	finput = open("eng.train","r")
	inputlines = finput.readlines()

	prev_word = ""
	prev_ne = ""

	dict_ne_words={}
	dict_ne_tags={}
	count_ne={}
	totalwords=0
	f=0

	for line in inputlines:
		lineset = line.split()
	
		if(len(lineset)==4):
		
			if f==1:
				if lineset[3] != prev_ne:
					f=0
					if len(prev_word) != 0:
					#	prev_word=snakecase(prev_word)
						if prev_ne not in dict_ne_words:
							dict_ne_words[prev_ne]={}
							dict_ne_words[prev_ne][prev_word]=1
						else:
							if prev_word not in dict_ne_words[prev_ne]:
								dict_ne_words[prev_ne][prev_word]=1
							else:						
								dict_ne_words[prev_ne][prev_word]+=1
						if prev_ne not in dict_ne_tags:
							dict_ne_tags[prev_ne]={}
							dict_ne_tags[prev_ne][prev_tag]=1
						else:
							if prev_tag not in dict_ne_tags[prev_ne]:
								dict_ne_tags[prev_ne][prev_tag]=1
							else:						
								dict_ne_tags[prev_ne][prev_tag]+=1
					if prev_ne not in count_ne:
						count_ne[prev_ne]=1
					else:
						count_ne[prev_ne]+=1
					totalwords+=1
					prev_ne = lineset[3]			
				else:
					prev_word = prev_word +"_"+ lineset[0].title()
	

			if f==0:
				temp = lineset[3].split('-')
				if len(temp)==1:
					prev_ne=temp[0]
				elif len(temp)==2:
					prev_ne=temp[1]
				prev_tag = lineset[2]
				f=1
				prev_word = lineset[0].title()
			
	#TESTING ==================================================================================================================

	ftest = open("eng.test","r")
	testlines = ftest.readlines()

	test_dict_ne_words={}
	test_dict_ne_tags={}
	testcount=0
	deno=0

	train_total_ne = dict_ne_words.keys()				

	fullsentence = ""


	for line in testlines:
		lineset = line.split()
	
		if(len(lineset)==4):
			if f==1:
				if lineset[2] != prev_tag:
					f=0
				#	prev_word=snakecase(prev_word)
					if prev_word not in test_dict_ne_words:
						test_dict_ne_words[prev_word]={}
						test_dict_ne_words[prev_word][prev_ne]=1
					elif prev_ne not in test_dict_ne_words[prev_word]:
						test_dict_ne_words[prev_word][prev_ne]=1
					else:
						test_dict_ne_words[prev_word][prev_ne]+=1
					

					prev_tag = lineset[2]			
				else:
					prev_word = prev_word +"_"+ lineset[0].title()


			if f==0:
				temp = lineset[3].split('-')
				if len(temp)==1:
					prev_ne=temp[0]
				elif len(temp)==2:
					prev_ne=temp[1]
				temp = lineset[2].split('-')
				if len(temp)==1:
					prev_tag=temp[0]
				elif len(temp)==2:
					prev_tag=temp[1]
				f=1
				prev_word = lineset[0].title()



	for line in testlines:
		lineset = line.split()
		if len(lineset) != 0: 
			fullsentence = fullsentence + " "+ lineset[0]

# uncomment for own POS tagger and comment nltk tokenizer and tagger
####	tagged=testing(fullsentence)

	tokenized = nltk.word_tokenize(fullsentence)
	tagged = nltk.pos_tag(tokenized)
	namedEnt = nltk.ne_chunk(tagged)
	print 
	i=0

	for name in namedEnt:
	
		lineset = name[0]
		if len(lineset)==2:
			prev_word= lineset[0]
			prev_tag= lineset[1]	
			new_ne_val = 0
			new_ne = ""					
		
			for n in train_total_ne:
				if n in count_ne:
					prob_ne= float(float(count_ne[n])/float(totalwords))	
				else:
					prob_ne = 0.001
				if n in dict_ne_words and prev_word in dict_ne_words[n]:
					prob_word=float(float((dict_ne_words[n][prev_word]))/float(totalwords))
				else:
					prob_word = 0.001
				if n in dict_ne_tags and prev_tag in dict_ne_tags[n]:
					prob_tag=float(float((dict_ne_tags[n][prev_tag]))/float(totalwords))
				else:
					prob_tag = 0.001
				final_prob = prob_ne*prob_tag*prob_word
	
				if new_ne_val < final_prob:
					new_ne_val=final_prob
					new_ne = n

			if prev_word in test_dict_ne_words and new_ne in test_dict_ne_words[prev_word]:
				testcount+=1 	
				if len(prev_word) > 1:

				#	x= snakecase(prev_word)
					x= prev_word					
					print ""
					print "Named Entity  ==========================>>>>>   "+ x
					querystring = """
					    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
					    SELECT ?label
					    WHERE { <http://dbpedia.org/resource/""" + x +"""> rdfs:label ?label }
					"""
					sparql.setQuery(querystring)
					sparql.setReturnFormat(JSON)
					results = sparql.query().convert()
			
					for result in results["results"]["bindings"]:
					    print "[ "+(result["label"]["value"])+" ]" + " " +"http://dbpedia.org/resource/"+ result["label"]["value"]
			else:
				deno+=1

#	print ""
#	print "Accuracy OF THE MODEL ======================================="
#	accuracy = (testcount*100)/(deno)
#	print accuracy


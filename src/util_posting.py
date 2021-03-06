# --------------------------------------------------------------------------------
# Import
import os 
import math
import operator
import collections
import math
import operator
import nltk
import string
import shutil
import re

from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import *
from util_index import tokenizeWord

from fagin import top_k_thresh
# --------------------------------------------------------------------------------
# Constant
SAVE_FILE  = 'saveFile'
DOC_LIST_PATH = "../data/util/docList"
POSTING_LIST_PATH = "../data/all_posting_list.txt"
STEMMER = PorterStemmer()

# --------------------------------------------------------------------------------

class PostingList(object):
    # Args :
    # qt is a string containing the query term this PL is made for
    # ordered_list is a list of (score, doc_id) ordered in decreasing score
    # access_dict (optional, can be computed from ordered_list) is a dict associating a doc to its score in this PL
    def __init__(self, qt, ordered_list, access_dict=None):
        self.qt=qt
        self.ordered_list = ordered_list
        if access_dict is not None:
            self.access_dict = access_dict
        else:
            self.access_dict = {}
            for score,doc in ordered_list:
                assert doc not in self.access_dict
                self.access_dict[doc] = score

        self.docs_visited = set()
        self.ordered_idx = 0

    # Returns : A (score, doc_index) tuple corresponding to the first non-visited entry in the ordered traversal
    def seek_next(self):
        while self.ordered_list[self.ordered_idx][1] in self.docs_visited:
            self.ordered_idx += 1
        return self.ordered_list[self.ordered_idx]

    # Returns : The score of the item preceding the next ordered accessed item
    def next_item_predecessor_score(self):
        tmp_idx = self.ordered_idx
        while self.ordered_list[tmp_idx][1] in self.docs_visited:
            self.ordered_idx += 1
        return self.ordered_list[tmp_idx-1][0]

    # Args :
    # doc_id is an integer containing the id of the document we want to mark as visited in the sorted access
    def mark_visited(self, doc_id):
        assert doc_id not in self.docs_visited
        self.docs_visited.add(doc_id)

    # Args :
    # doc_id is an integer containing the document id to lookup in the random access
    #
    # Returns : The score of the queried document in the PL
    def random_lookup(self, doc_id):
        return self.access_dict.get(doc_id,0.0)

def initialize_file_readers():
    """
    open the pieces of posting list that we have in the save_file directorie
    :return: an array of all file read for all file in the 'savefile' directory in the root
    """
    savefile_path = os.path.join(os.getcwd()+ "/../data/", SAVE_FILE)
    file_reader_list  = []
    for file in os.listdir(savefile_path):
        file_reader = open(os.path.join(savefile_path,file), "r")
        file_reader_list.append({"file_reader": file_reader, "last_read": { "word": "", "doc_score_list": []}})
    return file_reader_list



def close_file_readers(file_reader_last_read_list):
    """
    close all the posting list files that we readed
    :param file_reader_last_read_list: list of file that we readed path
    :return: Nothing
    """
    for file_reader in file_reader_last_read_list:
        file_reader["file_reader"].close()

def read_line_and_update(file_reader_and_last_read):
    """
    read a line in the files and parse the line to create a piece f posting list
    :param file_reader_and_last_read: the file that we want to update the head of the  reader
    :return: the updated head reader
    """
    read_line = file_reader_and_last_read["file_reader"].readline()
    line_list=str(read_line).split()
    if line_list != []:
        word = line_list[0]
        line_list = line_list[1:]
        doc_score_list = []
        line_list = iter(line_list)
        for item in line_list:
            doc_score_list.append({"doc": item, "score": next(line_list)})
        dic = {"word": word, "doc_score_list": doc_score_list}
        file_reader_and_last_read["last_read"] = dic
    else:
        file_reader_and_last_read["last_read"]={"word": "", "doc_score_list": []}
    return file_reader_and_last_read

def min_top_word(file_reader_last_read_list):
    """
    find the first element in the alphabetic order that if on a head reader
    :param file_reader_last_read_list: all the file head reader in the form of (file_reader, (word, {doc_id: score, ...}))
    :return: a string containing the first word in the
    """
    min_word = "|||"
    for file_reader_and_last_read in file_reader_last_read_list:
        if file_reader_and_last_read["last_read"]["word"] < min_word and file_reader_and_last_read["last_read"]["word"]\
         != "":
            min_word = file_reader_and_last_read["last_read"]["word"]
    return min_word

def add_doc_in_posting_list(word_posting_list, docs):
    """
    add a list of doc_id in the posting list word_posting_list
    :param word_posting_list: posting list in form of {doc_id: nb_occurence_word}
    :param docs: list of { "doc": doc_id, "score": score}
    :return: Nothing
    """
    for doc_score in docs:
        if doc_score["doc"] in word_posting_list.keys():
            word_posting_list[doc_score["doc"]] = int(doc_score["score"]) + int(word_posting_list[doc_score["doc"]])
        else:
            word_posting_list[doc_score["doc"]] = doc_score["score"]

def sort_and_cast_doc_in_posting_list(word_posting_list, itemgetterparam=1):
    """
    sort the posting list by score
    :param word_posting_list: the posting list in form of { doc_id: score, ...}
    :param itemgetterparam: element that will be use for the sort (1=score, 0=doc_id)
    :return: posting list in form of {doc_id: score}
    """
    temp = {}
    for key, val in word_posting_list.items():
        temp[int(key)] = float(val)
    otemp = sorted(temp.items(), key=operator.itemgetter(itemgetterparam))
    return dict(otemp)


def current_word_PL(current_word, file_reader_last_read_list, doc_dict, nb_doc):
    """
    build the posting list of a word
    :param current_word: the word associate to the posting list
    :param file_reader_last_read_list: the list of file_reader read head
    :param doc_dict: dict that containt all doc_id and the number of word in each doc {doc_id: nb_word, ...}
    :param nb_doc: number of doc in total
    :return: a posting list in form of  {key = doc , value = score }
    """
    word_posting_list = {} # { key = doc , value = score }
    for idx, file_reader_last_read in enumerate(file_reader_last_read_list):
        if file_reader_last_read["last_read"]["word"] == current_word:
            docs = file_reader_last_read["last_read"]["doc_score_list"]
            add_doc_in_posting_list(word_posting_list=word_posting_list, docs=docs)
            file_reader_last_read_list[idx]=read_line_and_update(file_reader_and_last_read=file_reader_last_read)
            for key, value in word_posting_list.items():
                tf = float(value) / doc_dict[int(key)]
                idf = math.log((float(nb_doc)/len(word_posting_list)),2)
                score  = tf*idf
                word_posting_list[key]=score       
            word_posting_list = sort_and_cast_doc_in_posting_list(word_posting_list=word_posting_list)
    return word_posting_list
    

def get_doc_dict(filename):
    """

    :param filename:
    :return:
    """
    doc_dict = {}
    file_reader = open(filename, "r")
    line = file_reader.readline()
    doc_id_nb_wd = line.split()
    while doc_id_nb_wd != []:
        doc_dict[int(doc_id_nb_wd[0])] = int(doc_id_nb_wd[1])
        line = file_reader.readline()
        doc_id_nb_wd = line.split()
    file_reader.close()
    return doc_dict

def current_word_PL(current_word, file_reader_last_read_list, doc_dict, nb_doc):
    """
    build the posting list of a word
    :param current_word: the word associate to the posting list
    :param file_reader_last_read_list: the list of file_reader read head
    :param doc_dict: dict that containt all doc_id and the number of word in each doc {doc_id: nb_word, ...}
    :param nb_doc: number of doc in total
    :return: a posting list in form of  {key = doc , value = score }
    """
    word_posting_list = {} # { key = doc , value = score }
    for idx, file_reader_last_read in enumerate(file_reader_last_read_list):
        if file_reader_last_read["last_read"]["word"] == current_word:
            docs = file_reader_last_read["last_read"]["doc_score_list"]
            add_doc_in_posting_list(word_posting_list=word_posting_list, docs=docs)
            file_reader_last_read_list[idx]=read_line_and_update(file_reader_and_last_read=file_reader_last_read)
    for key, value in word_posting_list.items():
        tf = float(value) / doc_dict[int(key)]
        idf = math.log((float(nb_doc)/len(word_posting_list)),10)
        score  = (tf*idf)
        word_posting_list[key]=score
    word_posting_list = sort_and_cast_doc_in_posting_list(word_posting_list=word_posting_list)
    return word_posting_list
    


def createPostingList():
    """
    Create all posting list into a file
    :return:
    """
    try :
        ##### peut etre à mettre dans une fonction
        file_reader_last_read_list = initialize_file_readers()
        for idx, file_reader_and_last_read in enumerate(file_reader_last_read_list):
            file_reader_last_read_list[idx]=read_line_and_update(file_reader_and_last_read=file_reader_and_last_read)
        current_word = min_top_word(file_reader_last_read_list=file_reader_last_read_list)
        final_file = open(POSTING_LIST_PATH, "w")
        ######

        doc_dict = get_doc_dict(DOC_LIST_PATH)
        nb_doc = len(doc_dict)

        ### autre function
        i = 0 
        while current_word != "|||":    
            current_PL = current_word_PL(current_word=current_word, file_reader_last_read_list=file_reader_last_read_list,\
             doc_dict=doc_dict, nb_doc=nb_doc ) 
            curent_string = ""
            for key, value in current_PL.items():
                curent_string = " " + str(key) + " " + str(value) + curent_string
            curent_string = current_word + curent_string
            final_file.write(curent_string + "\n")
            current_word = min_top_word(file_reader_last_read_list=file_reader_last_read_list)
            #if i %1000 == 0:
                #print(i/1000)
            i +=1
        ####
        
        final_file.close()
        close_file_readers(file_reader_last_read_list=file_reader_last_read_list)
    
    except Exception as ex:
        print(ex)
        final_file.close()
        close_file_readers(file_reader_last_read_list=file_reader_last_read_list)


def creat_posting_list_obj(posting_list_line):
    """
    Create a PostingList object with a line from the file that contain all the posing list
    :param posting_list_line: the line that will be used
    :return: the PostingList object
    """
    if  posting_list_line == "":
        return []
    
    qt = posting_list_line[0]
    tail = posting_list_line[1:]
    ordered_list = []
    access_dict = {}
    
    for i in range(0,len(tail)-1,2):
        doc_id = tail[i]
        score = tail[i+1]
        ordered_list.append((float(score),int(doc_id)))
        access_dict[int(doc_id)] = float(score)
        
    return PostingList(qt,ordered_list,access_dict)

def creat_posting_list_obj_list(query, filename=POSTING_LIST_PATH):
    """
     Create a list of PostingList object with a query string
    :param query: the query string
    :param filename: the path of the file which contain all the posting list
    :return: a list of PostingList object
    """
    posting_list_obj_list = []
    word_list = query.split()
    file_reader = open("../data/" + filename, "r")
    line = file_reader.readline()
    posting_list_line = line.split()
    
    while posting_list_line != []:
        if  posting_list_line[0] in word_list:
            posting_list_obj = creat_posting_list_obj(posting_list_line=posting_list_line)
            posting_list_obj_list.append(posting_list_obj)
        
        # read a new line. 
        line = file_reader.readline()
        posting_list_line = line.split()
    file_reader.close()
    return posting_list_obj_list

def handleFormatText(paragraphContent):
    """
    stem the string ntred and return in
    :param paragraphContent: the string that we want to stem
    :return: stemified string
    """
    # We tokenize and remove the stop word
    words = tokenizeWord(paragraphContent) 
    
    stemWords = []
    # We loop on each word.
    for word in words:
        stemWord = STEMMER.stem(word)
        
        # Selection on a part of string.
        stemWord = re.sub("[*\'\.+:,\`:/]", '', stemWord)
        if stemWord.isdigit() or len(stemWord) < 2:
            continue
            
        stemWords.append(stemWord)
    my_r_string = stemWords.pop(0)
    for word in stemWords:
        my_r_string += " "+str(word)
    return my_r_string


def manage_request(my_r_string, k=5):
    """
    find the k top doc id that corespond to the request 
    :param my_r_string: requeste string
    :param k: number of doc id wanted
    :return: list of (score,doc_id) order on score descending 
    """
    stem_r_str = handleFormatText(my_r_string)
    posting_lists = creat_posting_list_obj_list(stem_r_str)
    result = top_k_thresh(posting_lists, k, epsilon=0.0)
    return result
        

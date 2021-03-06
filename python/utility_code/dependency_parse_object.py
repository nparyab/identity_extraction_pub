__author__ = 'kennyjoseph'

import re
from nltk.stem import WordNetLemmatizer
from util import get_cleaned_text
from twitter_dm.utility.tweet_utils import get_stopwords
from nltk.corpus import wordnet as wn
import sys
stopwords = get_stopwords()

wordnet_lemmatizer = WordNetLemmatizer()
#import inflect

#inflect_engine = inflect.engine()

singular_map = {"children" : "child",
                "men" : "man",
                "women" : "woman",
                "people" : "person"
                }

class DependencyParseObject:
    def __init__(self, full_line=None, object_ids=[],  term_map=None, do_lemmatize=True, do_singular=True):
        self.cpostag = None
        self.features = []
        self.all_original_ids = []
        if full_line is not None:
            line = full_line.split("\t")
            self.line = line
            self.id = int(line[0])
            self.text = line[1]
            if line[2] != '_':
                self.lemma = line[2]
            self.postag = line[4]
            self.features = [x for x in line[5].replace("_","").split("|") if x != '']
            self.head = int(line[6])
            self.deprel = line[7]
            self.tweet_id = None
            self.dataset = None
            self.is_reply = None
            self.label = ''
            self.twitter_nlp_label = ''

            if len(line) == 8:
                pass
            elif len(line) == 9:
                self.label = line[8]
            elif len(line) == 11:
                self.tweet_id, self.dataset,self.is_reply = line[8:]
            elif len(line) == 12:
                self.tweet_id, self.dataset,self.is_reply,self.label = line[8:12]
            elif len(line) == 13:
                self.tweet_id, self.dataset, self.is_reply = line[10:13]
            elif len(line) == 14:
                self.tweet_id, self.dataset, self.is_reply, self.label = line[10:]
            elif len(line) == 15:
                self.tweet_id, self.dataset, self.is_reply, blah, self.label = line[10:]
            else:
                print 'UNRECOGNIZED FORMAT!!!!!!!!'
                print line
                sys.exit(-1)
            try:
                self.head_int = int(self.head)
            except:
                self.head_int = None


            wn_pos = penn_to_wn(self.postag)
            cleaned_text = get_cleaned_text(self.text)
            if do_lemmatize and wn_pos is not None:
                self.lemma = wordnet_lemmatizer.lemmatize(cleaned_text,wn_pos)
            else:
                self.lemma = wordnet_lemmatizer.lemmatize(cleaned_text)
            self.all_original_ids = [self.id]
            self.singular_form = cleaned_text
            if do_singular:
                if self.singular_form in singular_map:
                    self.singular_form = singular_map[self.singular_form]
                elif self.singular_form.endswith("s"):
                    self.singular_form = self.singular_form[:-1]


        elif len(object_ids):
            new_id = [obj_id for obj_id in object_ids if term_map[obj_id].head not in object_ids]
            assert len(new_id) == 1
            self.id = new_id[0]
            self.text = ' '.join([term_map[x].text for x in sorted(object_ids)])
            self.postag = ' '.join([term_map[x].postag for x in sorted(object_ids)])
            self.head = term_map[self.id].head
            self.deprel = ' '.join([term_map[x].deprel for x in sorted(object_ids)])
            self.lemma= ' '.join([term_map[x].lemma for x in sorted(object_ids)])
            self.label = ''
            self.singular_form = ' '.join([term_map[x].singular_form for x in sorted(object_ids)])
            original_term_maps = [term_map[x].all_original_ids for x in object_ids]
            self.all_original_ids = [item for sublist in original_term_maps for item in sublist]

    def __str__(self):
        return " ".join([self.text, str(self.id), self.postag, self.label])

    def __unicode__(self):
        s = " ".join([unicode(x) for x in [self.text,self.id,self.postag, self.head, self.label]])
        if self.deprel != "_":
            s += " " + self.deprel
        return s

    def get_conll_form(self):
        return "\t".join(unicode(x) for x in
                            [self.id,self.text,self.lemma,self.postag,self.postag,
                             '|'.join(self.features),self.head,self.deprel,'_','_',
                             self.tweet_id,self.dataset,self.is_reply,self.label])

    def word_features(self, is_prev_or_post):
        feats = []

        feats.append("word_low:" + self.text.lower())

        if self.deprel != "_":
            feats.append('DEPREL:' + self.deprel)

        feats.append('POS:' + self.postag,)
        #'LEN:' + str(len(self.text)),

        #if self.id == 1:
        #    feats.append('start_of_tweet')
        #elif self.id == sentence_len-1:
        #    feats.append('end_of_tweet')

        #feats.append('lemma:'+self.lemma)
        #feats.append('lemma_low:'+self.lemma.lower())

        if(len(self.text) >= 3) and not is_prev_or_post:
            x = 0
            feats.append("prefix=%s" % self.text[0:1].lower())
            feats.append("prefix=%s" % self.text[0:2].lower())
            #feats.append("prefix=%s" % self.text[0:3].lower())
            feats.append("suffix=%s" % self.text[len(self.text)-1:len(self.text)].lower())
            feats.append("suffix=%s" % self.text[len(self.text)-2:len(self.text)].lower())
            #feats.append("suffix=%s" % self.text[len(self.text)-3:len(self.text)].lower())

        #if self.text[0] == '@':
        #    feats.append('@')
        if self.text[0] == '#':
            feats.append('HT')

        ## subword features
        #feats.append('subword-1:'+self.text[:-1])
        #feats.append('subword-2:'+self.text[:-2])

        #if self.head_int:
        #    if self.head_int == -1:
        #        feats.append('NotInTree')
        #    else:
        #        feats.append('DependsOn')
        #else:
        #    feats.append('IsHead')

        #feats.append('REPLY:'+self.is_reply)
        #feats.append('TWIT_NLP:'+self.twitter_nlp_label)


        if re.search(r'^[A-Z]', self.text):
            feats.append('INITCAP')
        if re.match(r'^[A-Z]+$', self.text) and len(self.text) > 1:
            feats.append('ALLCAP')
        if re.match(r'.*[0-9].*', self.text):
            feats.append('HASDIGIT')
        if re.match(r'^[0-9]$', self.text):
            feats.append('SINGLEDIGIT')
        if re.match(r'^[0-9][0-9]$', self.text):
            feats.append('DOUBLEDIGIT')
        if re.match(r'.*-.*', self.text):
            feats.append('HASDASH')
        #if re.match(r'[.,;:?!-+\'"]', self.text):
        #    feats.append('PUNCTUATION')

        if is_prev_or_post:
            feats += [f for f in self.features if 'penntreebank' in f]
        else:
            feats += self.features

        return feats


    def join(self, list_of_objs):
        """
        Creates a new dependency parse object from a list of dependency parse objs.
        SHOULD NOT BE USED WHEN CREATING THE OBJECTS ... only useful for, e.g.,
        doing text lookups in dictionaries
        :param list_of_objs: A list of DependencyParseObjects that will be combined
        :return: self, a new dependnecy parse object
        """
        self.id = None
        #elf.cpostag = " ".join([x.cpostag for x in list_of_objs])
        self.text = ' '.join([x.text for x in list_of_objs])
        self.postag = ' '.join([x.postag for x in list_of_objs])
        self.head = None
        self.deprel = ' '.join([x.deprel for x in list_of_objs])
        self.lemma = ' '.join([x.lemma for x in list_of_objs])
        self.label = ' '.join([x.label for x in list_of_objs])
        self.all_original_ids = [x.id for x in list_of_objs]
        self.features = [y for x in list_of_objs for y in x.features]
        self.dataset = list_of_objs[0].dataset
        self.is_reply = list_of_objs[0].is_reply
        self.singular_form = ' '.join([x.singular_form for x in list_of_objs])
        return self


NOUN_TAGS = set(['NN', 'NNS', 'NNP', 'NNPS','N','^','S','Z','M'])#,'O'
def is_noun(tag):
    return tag in NOUN_TAGS\
           or len(set(tag.split(" ")).intersection(NOUN_TAGS)) > 0


def is_verb(tag):
    return tag in ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ','V','T']


def is_adverb(tag):
    return tag in ['RB', 'RBR', 'RBS','R']


def is_adjective(tag):
    return tag in ['JJ', 'JJR', 'JJS','A']


def penn_to_wn(tag):
    if is_adjective(tag):
        return wn.ADJ
    elif is_noun(tag):
        return wn.NOUN
    elif is_adverb(tag):
        return wn.ADV
    elif is_verb(tag):
        return wn.VERB
    return None

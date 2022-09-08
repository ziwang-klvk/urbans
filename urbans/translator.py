from typing import Dict, List
from .utils.tree_manipulation import translate_trees_grammar
from .utils.misc import remove_trailing_space
import nltk
from nltk.parse.chart import BottomUpLeftCornerChartParser as Parser

class Translator:
    """"""
    def __init__(self,
                 src_grammar: str,
                 src_to_tgt_grammar: Dict,
                 src_to_tgt_dictionary: Dict):
        """
        Initialize the translator
        Args:
            src_grammar (str): source language grammar written in nltk style
            E.g: src_grammar = \"""
                                S -> NP VP
                                NP -> PRP
                                VP -> VB PP
                                PP -> PB NP
                                NP -> CD NP1
                                NP1 -> JJ NN
                                PRP -> 'I'
                                VB -> 'go'
                                PB -> 'to'
                                CD -> 'a'
                                JJ -> 'good'
                                NN -> 'school'
                               \"""
            src_to_tgt_grammar (Dict): Transition between source grammar and target grammar as a dict
            E.g: src2target_grammar =  {
                                    "NP1 -> JJ NN": "NP1 -> NN JJ"
                                        }
            src_to_tgt_dictionary (Dict): Dictionary of word-by-word transition from src language to target language
            UPDATE: The dictionary now mapping the word based on its POS tag to avoid ambiguity
            E.g: en_to_jp_dict = {
                                "Vte":
                                    {
                                    "eat":"tabete",
                                    "drink":"nonnde",
                                    ...
                                    }
                                "Vorg":
                                    {
                                    "eat":"taberu",
                                    "drink":"nomu"
                                    }
                                }

            E.g: en_to_vi_dict = {
                                "I":"tôi",
                                "go":"đi",
                                "to":"tới",
                                "school":"ngôi_trường",
                                ...
                                 }
        """
        self.src_grammar = nltk.CFG.fromstring(self.__process_text_input(src_grammar))
        self.parser = Parser(self.src_grammar)
        self.src_to_tgt_grammar =  src_to_tgt_grammar
        self.src_to_tgt_dictionary = src_to_tgt_dictionary

    @staticmethod
    def __process_text_input(txt):
        return remove_trailing_space(txt)

    def parse_words(self, sentences: List[str] or str):
        """
        Parse the sentences to get the word translations should be provided in the dictionary
        Args:
            sentences (List[str]): A list of str-typed sentences
        """
        if isinstance(sentences,str):
            sentences = [sentences]
        
        tag_word_set = {}
        failed_sentences = []
        ambiguity_sentences = {}

        for sentence in sentences:
            sentence = self.__process_text_input(sentence)
            trees = self.parser.parse(sentence.split())
            list_trees = [tree for tree in trees]


            if len(list_trees) == 0:
                failed_sentences.append(sentence)
                continue
            # record sentences occuring ambiguity together with their parses
            if len(list_trees) > 1:
                ambiguity_sentences[sentence] = list_trees

            for t in list_trees:
                for tree_depth_2 in t.subtrees(lambda ptree: ptree.height() == 2):
                    # creat a set for new tag
                    if tree_depth_2.label() not in tag_word_set:
                        tag_word_set[tree_depth_2.label()] = set()
                    tag_word_set[tree_depth_2.label()].add(tree_depth_2.leaves()[0])
            
        print(f"Word parsing completed! {len(failed_sentences)} sentences failed. {len(ambiguity_sentences)} sentences occurred ambiguity.")
        
        return tag_word_set, failed_sentences, ambiguity_sentences


    def translate(self, sentences: List[str] or str, allow_multiple_translation = False):
        """
        Translate a list of sentences
        Args:
            sentences (List[str]): A list of str-typed sentences
        Returns:
            List[str]: A list of translated sentences
        """
        if isinstance(sentences,str):
            sentences = [sentences]

        translated_sentences = []
        failed_sentences = []
        # A trans_maps collect all translated versions occurred by ambiguities of sentences, together with their displacements. 
        trans_maps = []

        for sentence in sentences:
            sentence = self.__process_text_input(sentence)
            trees = self.parser.parse(sentence.split())
            list_trees = [tree for tree in trees]
            if len(list_trees) == 0:
                failed_sentences.append(sentence)
                continue
            trans_sentence, trans_map = translate_trees_grammar(list_trees, self.src_to_tgt_grammar, self.src_to_tgt_dictionary)
            if len(trans_map) > 1:
                trans_maps.append(trans_map)
            translated_sentences.append(trans_sentence)

        # String to display failed sentence
        failed_sentences = '\n'.join(failed_sentences)

        if len(failed_sentences) > 0:
            raise ValueError(f"Please check your grammar again, failed to parse these sentences: \n{failed_sentences}")

        return translated_sentences, trans_maps
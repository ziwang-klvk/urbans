from logging import raiseExceptions
import nltk
from nltk import ParentedTree as PTree
from typing import List
import random

def tree_to_ptree(tree: nltk.Tree):
    tree_str = tree.__str__()
    ptree = PTree.fromstring(tree_str)
    return ptree

def swap_tree_given_left(left_tree: nltk.Tree, displacement: List[int], new_words= List[str]):
    """Swap left node with right node within a parent node."""
    nodes = [left_tree]
    right_tree = left_tree.right_sibling()
    parent_tree = left_tree.parent()
    # Get all tree pointer
    for disp in displacement:
        # disp = -1 indicates that is a new word, skip
        if disp == -1:
            continue
        
        if right_tree == None:
            break
        
        nodes.append(right_tree)


        right_tree = right_tree.right_sibling()
        

    # Remove all siblings and left-most self
    for node in nodes:
        parent_tree.remove(node)

    # Append with new displacement
    for disp in displacement:
        # disp = -1 indicates that is a new word
        if disp == -1:
            new_word = PTree('NEW', [new_words.pop(0)])
            parent_tree.append(new_word)
        else:
            parent_tree.append(nodes[disp])

    return parent_tree
    

def build_grammar_str_from_left_most(tree: nltk.Tree):
    
    left_pt = tree.left_sibling()
    right_pt = tree.right_sibling()
    parent_pt = tree.parent()
    
    grammar_str = None

    if parent_pt != None:
        grammar_str = f"{parent_pt.label()} -> {tree.label()}"

        # Build grammar from leftmost node in the subtree
        if left_pt == None and right_pt != None :
            while right_pt != None:
                grammar_str += f" {right_pt.label()}"
                right_pt = right_pt.right_sibling()
    return grammar_str


def translate_tree_grammar(tree: nltk.Tree, grammar_substitutions: dict):
    """Translate tree grammar based on grammar substitution dict."""
    # Number of substitution done
    num_subs = 0
    # Convert tree to ParentedTree
    ptree = tree_to_ptree(tree)
    old_num_subs = -1

    # Loops until there no substitution left
    while num_subs != old_num_subs:
        old_num_subs = num_subs
        # Traverse through subtrees
        for sub in ptree.subtrees():
            # Create grammar string from left-most node. E.g: NP -> JJ NP,
            # in this case, JJ is left-most node
            grammar_str = build_grammar_str_from_left_most(sub)
            for src_grammar, tgt_grammar in grammar_substitutions.items():
                if grammar_str == src_grammar:
                    # Increment number of substitutions
                    num_subs += 1
                    # Calculate displacement between 2 grammar strings
                    disp, new_words = calculate_displacement(src_grammar,tgt_grammar)
                    # Change tree nodes positions thanks to new displacement
                    swap_tree_given_left(sub, disp, new_words)
 
    # The sentence is now list rather than string
    translated_grammar_sentence_list = ptree.leaves()

    # ADD: translated grammar sentence together with its tags
    word_to_tag_dic = []
    for tree_depth_2 in ptree.subtrees(lambda ptree: ptree.height() == 2):
        word_to_tag_dic.append(tree_depth_2.label())
    
    return translated_grammar_sentence_list, word_to_tag_dic, num_subs   
    
    return translated_grammar_sentence_list, num_subs

def translate_sentence_words(sentence, word_to_tag_dict, src_to_tgt_dictionary):
    words_list = []

    for word, tag in zip(sentence, word_to_tag_dict):
        word_dict = src_to_tgt_dictionary.get(tag,{})
        target_word = word_dict.get(word,word)

        if isinstance(target_word, list):
            target_word = random.choice(target_word)
        
        words_list.append(target_word)

    return ' '.join(words_list)

def translate_trees_grammar(list_trees: List[nltk.Tree], src_to_tgt_grammar, src_to_tgt_dictionary):

    # translated sentence map with number of grammar substitution found
    trans_map = {}

    for tree in list_trees:
        # Translate grammar
        trans_gram_sentence, word_to_tag_dict, num_subs = translate_tree_grammar(tree, src_to_tgt_grammar)

        # Translate words
        trans_lang_sentence = translate_sentence_words(trans_gram_sentence, word_to_tag_dict, src_to_tgt_dictionary)
        
        # Append to trans map
        trans_map[trans_lang_sentence] = num_subs
    # Return translation that has the most displacement, also the trans_map
    return max(trans_map, key=trans_map.get), trans_map

def calculate_displacement(src_grammar, tgt_grammar):
    """Calculate displacement between 2 grammar. E.g: S -> A B C to S -> B C A has displacement of [1 2 0]"""
    src_grammar_lst = src_grammar.split()
    tgt_grammar_lst = tgt_grammar.split()
    
    src_grammar_lst = src_grammar_lst[src_grammar_lst.index("->")+1:]
    tgt_grammar_lst = tgt_grammar_lst[tgt_grammar_lst.index("->")+1:]

    displacement = []
    new_words = []

    for word in tgt_grammar_lst:
        try:
          displacement.append(src_grammar_lst.index(word))
        except ValueError:
          # Resolve  ValueError: substring not found
          # Which indicates this is a new word
          displacement.append(-1)
          new_words.append(word)

    return displacement, new_words
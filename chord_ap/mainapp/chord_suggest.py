import requests
from bs4 import BeautifulSoup
import re

import numpy as np

import copy
from operator import itemgetter

def tension_check(chord_string, tension_string):

    ##length
    tension_length = len(tension_string)

    #-tension_string-
    if chord_string[:tension_length]==tension_string:
        return chord_string[tension_length:]
        
    #-add+tension_string-
    if chord_string[:3+tension_length]==("add"+tension_string):
        return chord_string[3+tension_length:]
        
    #-(+tension_string+)-
    if chord_string[:2+tension_length]==("("+tension_string+")"):
        return chord_string[2+tension_length:]
        
    return None

def chord_split(chord_string):
    ##translate chord_string into chord_vec
    ##initialized
    main_chord = "-"
    sub_chord = "-"
    base_chord = "-"
    seventh = "-"
    tension_number_list = ["6","9","11","13"]
    tension_var_list = ["-","-","-","-"]

    ##主調チェック
    main_chord = chord_string[:2]
    if main_chord[0] not in "ABCDEFG":
        return None##Chord ERROR
    else:
        if len(main_chord)==2:
            if main_chord[1] in "#♭":
                main_chord = chord_string[:2]#
                chord_string = chord_string[2:]
            else:
                main_chord = chord_string[0]#
                chord_string = chord_string[1:]
        else:
            main_chord = chord_string[0]#
            chord_string = chord_string[1:]

    if len(chord_string)==0:
        return [main_chord, sub_chord, base_chord, seventh] + tension_var_list

    #調合チェック
    if chord_string[:1]=="m":
        sub_chord = "m"
        chord_string = chord_string[1:]
    elif chord_string[:3]=="dim":
        sub_chord = "dim"
        chord_string = chord_string[3:]
    elif chord_string[:3]=="aug":
        sub_chord = "aug"
        chord_string = chord_string[3:]
    elif chord_string[:4]=="sus4":
        sub_chord = "sus4"
        chord_string = chord_string[4:]
    elif chord_string[:4]=="sus2":
        sub_chord = "sus2"
        chord_string = chord_string[4:]
    else:
        sub_chord = "-"

    if len(chord_string)==0:
        return [main_chord, sub_chord, base_chord, seventh] + tension_var_list

    #ベースコードチェック
    base_check = chord_string.split("/")
    if len(base_check)>2:
        return None
    elif len(base_check)==2:
        base_check_chord = base_check[1]
        if len(base_check_chord)==2:
            if base_check_chord[0] in "ABCDEFG" and base_check_chord[1] in "#♭":
                base_chord = base_check_chord
                chord_string = base_check[0]
            else:
                return None
        elif len(base_check_chord)==1:
            if base_check_chord[0] in "ABCDEFG":
                base_chord = base_check_chord
                chord_string = base_check[0]
            else:
                return None

    if len(chord_string)==0:
        return [main_chord, sub_chord, base_chord, seventh] + tension_var_list

    #テンションチェック
    while True:

        if len(chord_string)==0:
            return [main_chord, sub_chord, base_chord, seventh] + tension_var_list

        #セブンスチェック
        if chord_string[:1]=="7":
            seventh = "7"
            chord_string = chord_string[1:]
            continue
        if chord_string[:2]=="M7":
            seventh = "M7"
            chord_string = chord_string[2:]
            continue
            
        #テンション6,9,11,13チェック
        tension_checked_flag = False
        for i in range(len(tension_number_list)):
            checked_tension = tension_check(chord_string, tension_number_list[i])
            if checked_tension!=None:
                tension_var_list[i] = True
                chord_string = checked_tension
                tension_checked_flag = True##テンションありました
                break
        if tension_checked_flag==True:
            continue
                
        return None##どのテンションにも該当しない場合

def translate_string_to_chordvec(chord_string):

    chord_string_list = chord_string.split(",")
    chord_vec_list = []
    for current_chord in chord_string_list:
        chord_vec = chord_split(current_chord)
        if chord_vec!=None:
            chord_vec[0] = chord_standard(chord_vec[0])#♭を#形式に
            chord_vec[2] = chord_standard(chord_vec[2])#♭を#形式に
            chord_vec_list.append(chord_vec)
            
    return chord_vec_list
    
def chord_transpose(chord_main,transpose_param):
    
    chord_chain = ["A","A#","B","C","C#","D","D#","E","F","F#","G","G#"]
    
    chord_index = chord_chain.index(chord_main)
    
    return chord_chain[(chord_index+transpose_param)%12]
    
def chord_standard(chord_main):

    chord_chain = ["A","B","C","D","E","F","G"]
    
    if len(chord_main)==2 and chord_main[1]=="♭":
        chord_index = chord_chain.index(chord_main[0])
        if chord_index!=0:
            return chord_chain[chord_index-1]+"#"
        else:
            return chord_chain[-1]+"#"
    else:
        return chord_main
    
def eval_chords_coincidence(chord_vecA,chord_vecB):

    #check length
    if len(chord_vecA)!=len(chord_vecB) or len(chord_vecA)==0:
        return None
        
    #check dim(ex.Ddimは,C#調の特徴が強いため、C#にして調一致を計算するため、便宜上-1変換を行う.)
    for i in range(len(chord_vecA)):
        if chord_vecA[i][1]=="dim":
            chord_vecA[i][0] = chord_transpose(chord_vecA[i][0],-1)
        if chord_vecB[i][1]=="dim":
            chord_vecB[i][0] = chord_transpose(chord_vecB[i][0],-1)
    #check 主調
    for i in range(len(chord_vecA)):
        if chord_vecA[i][0]!=chord_vecB[i][0]:
            return -1
            
    #各コードの距離を計算-平均
    chord_distance = 0
    for i in range(len(chord_vecA)):
        current_chordA = chord_vecA[i]
        current_chordB = chord_vecB[i]
        #調合チェック
        if current_chordA[1]==current_chordB[1]:
            chord_distance += 0
        elif current_chordA[1] in "m-" and current_chordB[1] in "m-":
            chord_distance += 0.3
        elif (current_chordA[1]=="sus4" and current_chordB[1]=="sus2") or (current_chordA[1]=="sus2" and current_chordB[1]=="sus4"):
            chord_distance += 0.3
        else:
            name_index_list = ["-","m","aug","dim","sus4","sus2"]
            distance_list = [0,0.2,0.6,0.6,0.2,0.2]
            chord_distance += (distance_list[name_index_list.index(current_chordA[1])] + distance_list[name_index_list.index(current_chordB[1])])
        #セブンスチェック
        if current_chordA[3]!=current_chordB[3]:
            chord_distance += 0.1
        #6thチェック
        if current_chordA[4]!=current_chordB[4]:
            chord_distance += 0.1
        #9th,11th,13thチェック
        for i in [5,6,7]:
            if current_chordA[i]!=current_chordB[i]:
                chord_distance += 0.001
        
    return chord_distance/float(len(chord_vecA))
    
def translate_chordvec_to_string(chord_vec_list_get):

    chord_string_list = []
    for chord_vec_get in chord_vec_list_get:
    
        #"-"を"(blank)"に
        chord_vec = []
        for i in range(len(chord_vec_get)):
            if chord_vec_get[i]=="-":
                chord_vec.append("")
            else:
                chord_vec.append(chord_vec_get[i])
    
        chord_string = chord_vec[0]+chord_vec[1]+chord_vec[3]
        
        tension_name_list = ["","","","","6","9","11","13"]
        for i in [4,5,6,7]:
            if chord_vec[i]!="":
                chord_string += "("+tension_name_list[i]+")"
                
        chord_string_list.append(chord_string)
        
    return ",".join(chord_string_list)
    
def rank_search_chord(doc_chord_list,search_chord,boarder_value):

    search_len = len(search_chord)
    if search_len==0:
        return None
    
    ranking_chord_list = []
    for doc_chord in doc_chord_list:
        for i in range(len(doc_chord)-search_len+1):
            evaluation_value = eval_chords_coincidence(copy.deepcopy(doc_chord[i:i+search_len]),copy.deepcopy(search_chord))
            
            if (evaluation_value!=None and evaluation_value!=-1) and evaluation_value<=boarder_value:
                ranking_chord_list.append([doc_chord[i:i+search_len],doc_chord[i+search_len:i+search_len+5],evaluation_value])
            
    ranking_chord_list.sort(key=itemgetter(2))
        
    return ranking_chord_list

"""
print(["main","sub","base","7","6","9","11","13"])

chord_input_string_list = ["C,C,Cm,Cdim,Caug,Csus4,Csus2,Cdim(13),Caug9,CmM7","C,CmM7(13),C6(9),Caug(11)"]
chord_search_string = "C,C"

chord_vec_input_list = []
for chord_input_string in chord_input_string_list:
    chord_vec_input_list.append(translate_string_to_chordvec(chord_input_string))

chord_vec_list_search = translate_string_to_chordvec(chord_search_string)


ranking_chord_list = rank_search_chord(chord_vec_input_list,chord_vec_list_search,3)

for i in range(len(ranking_chord_list)):
    
    print("-----")
    print("match:"+translate_chordvec_to_string(ranking_chord_list[i][0]))
    print("suggest:"+translate_chordvec_to_string(ranking_chord_list[i][1]))
    print("eval:"+str(ranking_chord_list[i][2]))
    print("-----")
    
"""
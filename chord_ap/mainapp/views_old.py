from django.shortcuts import render
from django.views.generic import TemplateView, ListView

import requests
from bs4 import BeautifulSoup
import re

import numpy as np
import copy
from operator import itemgetter

from mainapp.models import Chords

# Create your views here.

###クローリング用###

def get_contents_only(strings):
    strings = str(strings)
    while(True):
        start = strings.find("<")
        end = strings.find(">")
        if start==-1 or end==-1:
            return strings
        strings = strings[:start] + strings[end+1:]

def get_link_only(strings):
    strings = str(strings)
    start = strings.find('href="')
    end = strings.rfind('">')
    return strings[start+6:end]

def check_true_chord(chord_string):
    #re.match("[A-G1-9/Mmaugdim-]*", chord_string)
    if "&" in chord_string:
        return False
    elif "|" in chord_string:
        return False
    elif "." in chord_string:
        return False
    elif ">" in chord_string:
        return False
    elif ("(" in chord_string) or (")" in chord_string):
        return False
    else:
        return True

def exec_crawling():

    ##初期化##
    Chords.objects.all().delete()

    root_address = "https://ja.chordwiki.org"
    
    for page_num in range(1,5):##ここ改善の必要あり

        html_get = requests.get('https://ja.chordwiki.org/list/'+str(page_num)+'.html')
        soup = BeautifulSoup(html_get.content, "html.parser")

        ##get title link list##
        title_list = soup.find('ul')
        title_link_list = []
        for title_string in title_list.find_all(['a']):
            current_music_info = []
            current_music_info.append(get_contents_only(title_string))
            current_music_info.append(root_address+get_link_only(title_string))
            title_link_list.append(current_music_info)

        for j in range(len(title_link_list)):

            html_get = requests.get(title_link_list[j][1])

            soup = BeautifulSoup(html_get.content, "html.parser")

            title_name = soup.select('h1.title')
            subtitle_name = soup.select('h2.subtitle')
            chord_string_list = soup.select('span.chord')

            chord_list = []
            for i in range(len(chord_string_list)):
                chord_string = str(chord_string_list[i])
                start = chord_string.find(">")
                end = chord_string.rfind("<")
                chord_string = chord_string[start+1:end]
                if check_true_chord(chord_string)==True:
                    chord_list.append(chord_string)
                    
            chord_list = translate_string_to_chordvec(chord_list)
                    
            title_name = get_contents_only(title_name[0])
            subtitle_name = get_contents_only(subtitle_name[0])
            Chords.objects.create(title=title_name,subtitle=subtitle_name,link=title_link_list[j][1],chords=chord_list)
            print(title_name)
            print(subtitle_name)
            print(chord_list)
            
    return

def translate_string_to_chordvec(chord_string_list):

    chord_vec_list = []
    for current_chord in chord_string_list:
        chord_vec = chord_split(current_chord)
        if chord_vec!=None:
            chord_vec[0] = chord_standard(chord_vec[0])#♭を#形式に
            chord_vec[2] = chord_standard(chord_vec[2])#♭を#形式に
            chord_vec_list.append(chord_vec)
            
    return chord_vec_list
    
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
    
##suggested chord##
    
def chord_transpose(chord_main,transpose_param):
    
    chord_chain = ["A","A#","B","C","C#","D","D#","E","F","F#","G","G#"]
    
    chord_index = chord_chain.index(chord_main)
    
    return chord_chain[(chord_index+transpose_param)%12]
    
def eval_chords_coincidence(chord_vecA,chord_vecB):

    #check length
    if len(chord_vecA)!=len(chord_vecB) or len(chord_vecA)==0:
        return None
        
    #check dim(ex.Ddimは,C#調の特徴が強いため、C#にして調一致を計算するため、便宜上-1変換を行う.)
    print(chord_vecA)
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
    for current_doc_chord_info in doc_chord_list:
        doc_chord = current_doc_chord_info[0]
        doc_title = current_doc_chord_info[1]
        doc_subtitle = current_doc_chord_info[2]
        doc_link = current_doc_chord_info[3]
        
        for i in range(len(doc_chord)-search_len+1):
            evaluation_value = eval_chords_coincidence(copy.deepcopy(doc_chord[i:i+search_len]),copy.deepcopy(search_chord))
            
            if (evaluation_value!=None and evaluation_value!=-1) and evaluation_value<=boarder_value:
                #1:search chord
                #2:suggest chord
                #3:eval value
                #4:title
                #5:sub title
                #6:link
                #7:position
                ranking_chord_list.append([doc_chord[i:i+search_len],doc_chord[i+search_len:i+search_len+5],evaluation_value,doc_title,doc_subtitle,doc_link,str(i+1)])
            
    ranking_chord_list.sort(key=itemgetter(2))
        
    return ranking_chord_list
    

def suggested_chord(input_chord):

    chord_set_all = Chords.objects.all()
    
    ##prepare for input list
    chord_doc_vec_list = []
    for i in chord_set_all:
        chord_doc_vec_list.append([i.chords,i.title,i.subtitle,i.link])
    
    ##search
    ranking_chord_list = rank_search_chord(chord_doc_vec_list,translate_string_to_chordvec(input_chord.split(",")),100000)
    
    print(ranking_chord_list)

    return Chords.objects.all()[1].title+",C"

###main###

def perse_get_query_params(req):

    ##return get query
    if "chord" in req.GET:
        chord = req.GET.get("chord")
    else:
        chord = None
    if "Crawling" in req.GET:
        crawling = req.GET.get("Crawling")
    else:
        crawling = None

    return chord, crawling
    

class main_page(ListView):
    template_name = "mainapp/main_page.html"

    def get_queryset(self):
        query_set = self.request##ここで返答クエリを作成してください！！
        return query_set

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["input_chord"], crawling_check = perse_get_query_params(self.request)
        if crawling_check!=None:
            exec_crawling()
        if context["input_chord"]!=None:
            context["output_chord"] = suggested_chord(context["input_chord"])
        return context

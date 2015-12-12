from __future__ import division
from collections import defaultdict
import sys, json, glob, codecs, os

# usage python parse_json "json/*.json" 
# where the root json file contains character coocurrence json

nodes_list = []

def retrieve_nodes():
    """Retrieve all nodes from all cooccurrence json files"""
    play_nodes = defaultdict(list)
    for i in glob.glob("json/*.json"):
        with open(i) as j:
            j = json.load(j)
            for n in j["nodes"]:
                play_nodes[i].append(n)
    return play_nodes

def character_attributes(play_nodes):
    """Write df and json for character entrances and words spoken"""
    with codecs.open("df",'w','utf-8') as df_out:
        with open("words_by_entrance.json",'w') as json_out: 
            for c, play in enumerate(play_nodes):
                nodes = play_nodes[play]

                # write headers on first pass
                if c == 0:
                    df_out.write("play" + "\t" + "\t".join(
                        k for k in nodes[0]) + "\n")

                # write df                
                for n in nodes:
                    df_out.write(os.path.basename(play) + "\t" 
                         +"\t".join(unicode(n[k]) for k in n) + "\n")

                # collect character-level json of words spoken and entrances
                for n in nodes:                
                    if n["gender"] == 3:
                        continue
                    # add play to dictionary
                    n["play"] = os.path.basename(play).replace(".json",'')

                    nodes_list.append(n) 

                # write character-level json of words spoken and entrances
                json.dump(nodes_list, json_out)
    
def play_attributes(play_nodes):
    """Write df and json for play-level character attributes"""
    # collect stats from each character to assemble play-level insights
    d = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    d2 = defaultdict(lambda: defaultdict(lambda: defaultdict(list))) 
    for play in play_nodes:
        nodes = play_nodes[play]
        for n in nodes:
            if n["gender"] == 3:
                continue

            d[os.path.basename(play)][n["gender"]]["entrance"].append(n["entrance"])
            d[os.path.basename(play)][n["gender"]]["words"].append(n["words"])
            d2[os.path.basename(play)][n["gender"]]["entrance"].append(
                {"name":n["name"],"entrance": n["entrance"]})
            d2[os.path.basename(play)][n["gender"]]["words"].append(
                {"name":n["name"],"entrance":n["words"]})
       
    min_max_json_list = []
    with open("high-level-stats",'w') as stat_out: 
        # generate play-level statistics df
        for play in d:
            for gender in d[play]:
                mean_entrance = ( sum(d[play][gender]["entrance"]) 
                    / len(d[play][gender]["entrance"]) )
                min_entrance = min(d[play][gender]["entrance"])
                max_entrance = max(d[play][gender]["entrance"])     
                mean_words = ( sum(d[play][gender]["words"]) 
                    / len(d[play][gender]["words"]) )
                min_words = min(d[play][gender]["words"])
                max_words = max(d[play][gender]["words"])
                vals_to_write = [os.path.basename(play), gender, mean_entrance, 
                    min_entrance, max_entrance, mean_words, min_words, max_words]
                stat_out.write("\t".join(str(v) for v in vals_to_write) + "\n")
   
                for character_dict in d2[play][gender]["entrance"]:
                    if character_dict["entrance"] == min_entrance:
                        min_char = character_dict
                    elif character_dict["entrance"] == max_entrance:
                        max_char = character_dict

                min_max_json_list.append( {"play":play.replace(".json",""),
                    "gender":gender,
                    "min":{"name":min_char["name"],"val":min_char["entrance"]},
                    "max":{"name":max_char["name"],"val":max_char["entrance"]}}
                )

    with open("min_max_words.json",'w') as min_max_words_out:
        json.dump(min_max_json_list, min_max_words_out) 
     
if __name__ == "__main__":
            
    play_nodes = retrieve_nodes()
    character_attributes(play_nodes)
    play_attributes(play_nodes)    

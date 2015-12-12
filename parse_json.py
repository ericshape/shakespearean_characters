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
    
def generate_attribute_dict(play_nodes):
    """Write df and json for play-level character attributes"""
    # collect stats from each character to assemble play-level insights
    d = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for play in play_nodes:
        nodes = play_nodes[play]
        for n in nodes:
            if n["gender"] == 3:
                continue
            d[os.path.basename(play)][n["gender"]]["entrance"].append(
                {"val": n["entrance"], "name": n["name"]})
            d[os.path.basename(play)][n["gender"]]["words"].append(
                {"val": n["words"], "name": n["name"]})
    return d

def write_vals(d):
    """Write play-level characteristics of character-level properties"""
    stats_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict())))
    with open("high-level-stats",'w') as stat_out: 
        words_json = []
        entrance_json = []
        # generate play-level statistics df
        for play in d:
            for gender in d[play]:
                for feature in d[play][gender]:
                    max_obs = max(d[play][gender][feature], key=lambda x:x['val'])
                    min_obs = min(d[play][gender][feature], key=lambda x:x['val'])

                    # In the event of tie for high and low assign one tie 
                    # member to high and one to low (unless it's a one-character tie)
                    if min_obs == max_obs:
                        for character in d[play][gender][feature]:
                            if character["val"] == max_obs["val"]:
                                if character["name"] != max_obs["name"]:
                                    print "There was a tie between", min_obs, max_obs,
                                    print "for feature", feature, "in", play,
                                    print "assigning", character, "to max and", min_obs,"to min"
                                    print "\n"
                                    max_obs = character
                                                            
   
                    stat_out.write("\t".join(str(v) for v in [play, gender, feature, max_obs["val"], min_obs["val"]]) + "\n")
                              
                    if feature == "words":
                        words_json.append({"gender": gender,
                        "play": play,
                        "max": {"val": max_obs["val"], "name": max_obs["name"]},
                        "min": {"val": min_obs["val"], "name": min_obs["name"]}})
                        
                    elif feature == "entrance":
                        entrance_json.append({"gender": gender,
                        "play": play,
                        "max": {"val": max_obs["val"], "name": max_obs["name"]},
                        "min": {"val": min_obs["val"], "name": min_obs["name"]}})
                
        with open("min_max_words.json",'w') as words_json_out:
            json.dump(words_json, words_json_out)
        with open("min_max_entrance.json",'w') as entrance_json_out:
            json.dump(entrance_json, entrance_json_out)

if __name__ == "__main__":
            
    play_nodes = retrieve_nodes()
    character_attributes(play_nodes)
    d = generate_attribute_dict(play_nodes)   
    write_vals(d)


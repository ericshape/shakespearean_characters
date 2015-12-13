from __future__ import division
from networkx.algorithms.approximation.dominating_set import min_weighted_dominating_set
from networkx.algorithms.approximation import min_edge_dominating_set
from networkx.algorithms.cluster import average_clustering
from collections import defaultdict
from itertools import combinations
from numbers import Number
import codecs, urllib2, networkx, igraph, os, json, glob, operator

class autovivify(dict):
    """Pickleable class to replicate the functionality of collections.defaultdict"""
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value
    
    def __add__(self, x):
        """Override addition for numeric types when self is empty"""
        if not self and isinstance(x, Number):
            return x
        raise ValueError
        
    def __sub__(self, x):
        """Also provide subtraction method"""
        if not self and isinstance(x, Number):
            return -1 * x 
        raise ValueError

def retrieve_cooccurrences():
    """Retrieve characters per scene for each play"""
    url = "https://raw.githubusercontent.com/duhaime/mining_the_bard/master/1.1_shakes_analysis/shakespeare_character_counts_by_scene.txt"
    response = urllib2.urlopen(url)
    html = response.read()
    delimited = [r.split("\t") for r in html.split("\n")[:-1]]
    return delimited

def retrieve_character_genders(glob_path_to_xml, clean_names=1):
    """Return a dictionary mapping character name to gender"""
    character_to_gender = autovivify()
    for folger_xml in glob.glob(glob_path_to_xml):
        with codecs.open(folger_xml, 'r', 'utf-8') as f:
            names = f.read().split('person xml:id="')[1:]
            for n in names:
                name = n.split("_")[0]
                if clean_names == 1:
                    name = clean_character_name(name)                
                # Use Folger markup to retrieve gender
                try:
                    gender = int(n.split('<sex value="')[1].split('"')[0])
                except:
                    continue
                character_to_gender[os.path.basename(folger_xml)][name] = gender
    return character_to_gender

def retrieve_character_entrances(clean_names=1):
    """Return a mapping from character name to entrance in play"""
    delimited = retrieve_cooccurrences()
    previous_play = None
    previous_words = 0
    character_appearances = {}
    for r in delimited[:-1]:
        play = r[0]
        if play != previous_play:
            previous_words = 0
        previous_play = play
        for c in r[4].split():
            if clean_names==1:
                c = clean_character_name(c)
            if play not in character_appearances.keys():
                character_appearances[play] = {}
            if c not in character_appearances[play].keys():
                print play, c, previous_words
                character_appearances[play][c] = previous_words

        # col[3] of delimited reflects words spoken while 
        # characters col[4] were on stage, so add their
        # words to the previous words 
        previous_words += int(r[3])
        

    return character_appearances            

def words_by_character(clean_names=1):
    """Return a dictionary mapping the number of words spoken by each character"""
    urla = "https://raw.githubusercontent.com/duhaime/mining_the_bard/master/"
    urlb = "4.1_find_distribution_in_speakers/speaking_distribution_by_play.txt"
    url = urla + urlb
    response = urllib2.urlopen(url)
    html = response.read()
    words_per_char = autovivify()
    delimited = [r.split("\t") for r in html.split("\n")[:-1]]
    for r in delimited:
        play = r[0]
        character = r[1]
        words_spoken = r[2]
        if clean_names == 1:
            character = clean_character_name(character)
        words_per_char[play][character] = int(words_spoken)
    return words_per_char
       
def clean_character_name(character_name):
    """To avoid clutter, remove numbered characters and shorten character names"""
    if "." in character_name: 
        if character_name.split(".")[-1].isdigit():
            return
        elif all([i.isupper() for i in character_name.replace(".","")]):
            return
        else: 
            return character_name.split(".")[-1]
    elif all([i.isupper() for i in character_name.replace(".","")]):
        return character_name[0] + ''.join(i.lower() for i in character_name[1:])
    else:
        return character_name

def create_cooccurrence(clean_names=1):
    """Use characters who coappear in a scene to update the cooccurrence dict"""
    cooccurrence = autovivify()
    chars_per_scene = retrieve_cooccurrences()
    for r in chars_per_scene:
        play = r[0]
        if clean_names == 1:
            chars = [clean_character_name(i) for i in r[4].split() if clean_character_name(i)]
        else:
            chars = r[4].split()
        for c in combinations(chars, 2):
            cooccurrence[play][c[0]][c[1]] += 1
    return cooccurrence

def create_counter_dictionary():
    """Return a hash table that autoincrements as it's fed new strings"""
    dictionary = defaultdict()
    dictionary.default_factory = lambda: len(dictionary)
    return dictionary

def reverse_dictionary(d):
    """Read in a d from k:v and return a dictionary mapping v:k"""
    return {v: k for k, v in d.iteritems()}

def create_graph(character_cooccurrence):
    """Transform a play-level cooccurence dict into a graph and character id dict"""
    G = networkx.Graph()
    extant_nodes = []
    character_to_id = create_counter_dictionary()

    for char1 in character_cooccurrence.iterkeys():
        if char1 not in extant_nodes:
            extant_nodes.append(char1)
            G.add_node(character_to_id[char1], label=char1)
            
        for char2 in character_cooccurrence[char1].iterkeys():
            if char2 not in extant_nodes:
                extant_nodes.append(char2)
                G.add_node(character_to_id[char2], label=char2)
                    
            G.add_edge(character_to_id[char1], character_to_id[char2], 
                weight=character_cooccurrence[char1][char2])
            
    # Return id_to_character (or reversal of character_to_id) for label retrieval later on
    id_to_character = reverse_dictionary(character_to_id)
    
    return G, id_to_character

def networkx_to_igraph(G, directed=False):
    """Read in a networkx graph and return an igraph with the same data""" 
    ig = igraph.Graph(directed=directed)
    ig.add_vertices( len(G.nodes()) )
    ig.add_edges([(G.nodes().index(edge[0]),G.nodes().index(edge[1])) for edge in G.edges()])
    return ig

def community_detection(G, id_to_character):
    """Read in a networkx graph and return the community of each character in that graph"""
    ig = networkx_to_igraph(G)
    character_to_group = {}
    groups = ig.community_fastgreedy() 
    clusters = groups.as_clustering()
    membership_array = clusters.membership
    for index_position, group in enumerate( membership_array ):
        character = id_to_character[index_position]
        character_to_group[character] = group
        
    return character_to_group

def triangular_number(n):
    """Return the factorial number (using addition rather than multiplication) of n"""
    val = n
    for i in xrange(n):
        val += i
    return val

def retrieve_graph_attributes(G):
    """Read in a graph and return an array of graph statistics"""
    n_nodes = networkx.number_of_nodes(G)
    n_edges = networkx.number_of_edges(G)
    min_dom_set = min_weighted_dominating_set(G)
    min_edge_dom_set = min_edge_dominating_set(G)
    ramsey = networkx.algorithms.approximation.ramsey.ramsey_R2(G)
    assortativity = networkx.algorithms.assortativity.degree_assortativity_coefficient(G)
    pearson = networkx.algorithms.assortativity.degree_pearson_correlation_coefficient(G)
    neighbor = networkx.algorithms.assortativity.neighbor_degree.average_neighbor_degree(G)
    average_connectivity = networkx.algorithms.assortativity.average_degree_connectivity(G)
    knn = networkx.algorithms.assortativity.connectivity.k_nearest_neighbors(G)
    centrality = networkx.algorithms.centrality.degree_alg.degree_centrality(G)
    closeness = networkx.algorithms.centrality.closeness.closeness_centrality(G)
    betweenness = networkx.algorithms.centrality.betweenness.betweenness_centrality(G)
    communicability = networkx.algorithms.centrality.communicability_alg.communicability(G)
    estrada = networkx.algorithms.centrality.communicability_alg.estrada_index(G)
    shortest = networkx.algorithms.shortest_paths.shortest_path_length(G)
   
    # Of all possible edges in the graph, find the percent of missing edges
    missing_edges = 1 - ( n_edges / triangular_number(n_nodes) )

    return (n_nodes, n_edges, len(min_dom_set), len(min_edge_dom_set), ramsey, assortativity,  
        pearson, average_connectivity, knn, centrality, closeness, betweenness, communicability, 
        estrada, shortest, missing_edges)

def write_network_stats(play_title, network_stats):
    """Read in graph stats and play title and write the stats to disk"""
    with codecs.open("network_stats.txt",'a','utf-8') as stats_out:
        stats_out.write( play_title + "\t" + "\t".join(str(i) for i in network_stats) + "\n" )

def write_cooccurrence_json(cooccurrence, character_groups, gender_dict):
    """Produce json in miserables.json format expected to by D3"""
    
    nodes_list = []
    for i in id_to_character:
        name  = id_to_character[i]
        format_name = ".".join(name.split())
        group = character_groups[name]
        character_entrance = character_entrances[play][name]
 
        character_words = words_per_character[play][name]
        try:
            float(character_words)
        except TypeError:
            character_words = 100
    
        try:
            character_gender = int(gender_dict[name])
        except TypeError:
            character_gender = 3    

        character_dict = {"name":format_name, "group":group, 
            "words":character_words, "entrance": character_entrance,
            "gender":character_gender}
        nodes_list.append(character_dict)

    links_list = []
    for i in id_to_character:
        for j in id_to_character:
            i_name = id_to_character[i]
            j_name = id_to_character[j]
            if j_name in cooccurrence[i_name].keys():                
                link_dict = {"source":i,"target":j,"value":cooccurrence[i_name][j_name]}
                links_list.append(link_dict) 

    cooccurrence_json = {"nodes":nodes_list, "links":links_list}
   
    with open("json/" + play.replace(".xml","") + ".json", 'w') as json_out:
        json.dump(cooccurrence_json, json_out)

def make_json_dir():
    """If there isn't a directory named "json" in cwd, make one"""
    if not os.path.exists("json"):
        os.makedirs("json")

if __name__ == "__main__":
    # State globals, where cn = clean_names option
    cn = 1
    folger_xml_path = "./XML/*.xml"
    
    make_json_dir()
    words_per_character = words_by_character(clean_names=cn) 
    character_entrances = retrieve_character_entrances(clean_names=cn)
    character_to_gender = retrieve_character_genders(folger_xml_path, clean_names=cn) 
    cooccurrence = create_cooccurrence(clean_names=cn)
    for play in cooccurrence.iterkeys():
        graph, id_to_character = create_graph(cooccurrence[play])
        communities = community_detection(graph, id_to_character)        
        graph_attributes = retrieve_graph_attributes(graph)     
        write_network_stats(play, graph_attributes)
        write_cooccurrence_json(cooccurrence[play], communities, character_to_gender[play])


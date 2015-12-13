###Visualizing Shakespearean Characters

This repo contains utilities used to collect and visualize data on Shakespeare's characters. 

`utils/shakespearean-networks.py` requires the Folger Shakespeare Digital Texts collection of [Shakespeare XML]("http://www.folgerdigitaltexts.org/"). Once those files are downloaded and unzipped, one should specify a glob path to the XML directory in the following line:

`folger_xml_path = "./XML/*.xml"`

Once this path is set, one can run `python shakesperean-networks.py`, which will generate an output directory entitled "json" that contains the json to be fed to the cooccurrence visualization. 

To generate the json for the scatter plots, one can run `python parse_json.py "json/*.json"` on that json directory.

To visualize the plots locally, just start a webserver from the directory in which `index.html` is located using:

`python -m SimpleHTTPServer`

This will start a server on port 8000 by default. Index.html will then make calls to the json files loaded in Amazon Web Service's S3 servers. If you open a browser and navigate to:

`localhost:8000`

you should be able to see the visualizations.  

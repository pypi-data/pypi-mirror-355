[![pipeline status](https://gitlab.inria.fr/pydisk/examples/vizitig/badges/main/pipeline.svg)](https://gitlab.inria.fr/pydisk/examples/vizitig/-/commits/main) 
[![coverage report](https://gitlab.inria.fr/pydisk/examples/vizitig/badges/main/coverage.svg)](https://gitlab.inria.fr/pydisk/examples/vizitig/-/commits/main) 
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)


Vizitig is:

- A command line interface (CLI) to administrate, build and annotate genomic or transcriptomic graph and update them
- A Web interface to vizualize and manipulate those graphs
- A Python library for a programmatic pythonic interaction with graphs

# Installation

`Vizitig` can be installed as 

```bash
pip install vizitig
```

This should work for major distributionss.
It is however mostly battle tested on Linux. 

Some system (as debian) will prevent you to run this
command as it could be incompatible with your system
Python librairie. To avoir the issue, you should run
the command [within a virual environnement](https://docs.python.org/3/library/venv.html)

## Installation of vizitig upstream 

To install the latest version of vizitig (upstream), use the following instructions. 
It will clone the code install all required dependencies for vizitig to run. Make sure to have the python venv package installed.  


```
git clone https://gitlab.inria.fr/pydisk/examples/vizitig
cd vizitig
make install
source venv/bin/activate
``` 

Remark that upstream vizitig might have some unstable features.
To contribute to vizitig code base you also need to install other
tools (such as ruff, mypy, etc.). To install all those dependencies:

```
pip install .[all]
``` 


## Vizitig custom binaries

Some part of Vizitig are pre-compiled librariries written on rust. This library
will be automatically installed on your computer if you have cargo installed.
This library is called Vizibridge. Vizitig should run without it but it will be
vastly slower on build and annotation task. Additionnal indexes are provided by
this library.

```
pip install vizibridge
``` 

To check if vizibridge is installed you can run

```
pip show vizibridge
``` 

If it is not installed, you can install vizibridge for your system
with the following script. Be aware that this will install the full rust
compilation tool chain.

The following script assumes `pip` and `venv` are already installed.


The following `bash` script install `vizibridge` on your machine with `bash`.

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.bashrc # this is to refresh the path 
cargo install maturin
python3 -m venv venv
source venv/bin/activate
git clone https://gitlab.inria.fr/cpaperma/vizibridge
cd vizibridge; maturin build --release
pip install target/wheels/vizibridge**.whl
```
# The visual interface 

With the venv activated, type 

```
vizitig run 
``` 

and the web-interface will appear. Note that on some distributions of Ubuntu, gnome cannot access the browser so you will need to open the brower yourself and go to this address : "http://localhost:4242". The issue may appear on other distributions as well. 

In the graphical user interface (GUI), you can select, rename, copy, download or delete existing graphs. Other transformations to the graphs can be made, for example coloring or annotating operations (see dedicated chapters). Users can also access saved visualisation : once the graph is loaded, visual operations can be applied on it (see dedicated chapter). The state of this visualisation can be saved using the "Save" blue button. 

Back in the first interface page, the users can also add graphs (exports from an other instance of vizitig) or a BCALM file that will be ingested. Users can name their graphs. Drag and drop works for sending files in Vizitig. 

# Visualisation states

By default, two visualisation modes open : the band graph and the table. The table has an action set by default, which is the "selection not hide". In other terms, the table will show you the selection made in other tabs. 

The band graph is a graph visualisation where bands represent node (where the size of the band is proportional to the size of the sequence associated to a node) and connections between bands represent the edges. The former version of the band graph (the simple graph) does the opposite : node are represented by squares and edges are materialized between nodes. 

The graph visualisations benefit from defaut function. Start and Stop buttons will activate/deactivate the dynamicity of the visualisation. The Center button will center the user's POV on the baricenter of the graph. The Linearize button will help unfold the currently loaded nodes visualy. Note that this implementation is likely quadratic and will start taking a lot of time above 2000 loaded nodes. 

# The CLI

Before running any CLI command, you should activate the virtual environment in which Vizitig runs. 
To do so, you can type the following while in the vizitig folder: 


```bash
source venv/bin/activate
```

The CLI is rather self contained with documentation:

```
vizitig -h
```

Will provides the following:

```
usage: vizitig [-h] {info,rename,add,rm,index,color,annotate,build,run} ...

A CLI interface to vizitig

positional arguments:
  {info,rename,add,rm,index,color,annotate,build,run}
    info                get information about ingested graphs
    rename              Rename a graph
    add                 Add an already built Vizitig Graph
    rm                  Remove an already built Vizitig Graph
    index               Index utilities of graph.
    color               Color an existing graph. There are several ways to use this feature : -vizitig color -f file_name -m color_name -> Will color the graph with whatever is in the
                        provided file -vizitig color --folder folder_name -> Will color the graph with every file in the provided folder. The name of the color will be the name of the file
                        for each file -vizitig color --folder folder_name -m color_name -> Same, but the name of the color will be color_name for all files -vizitig color --csv file.csv ->
                        Will use a csv file to color the graph. Csv must respect the following format (tabèseparated): /path/to/file1 red "Sample 1 - control group" /path/to/file2 green
                        "Sample 2 - condition 1" /path/to/file3 blue "Sample 3 - condition 2"
    annotate            Add annotations to a given graph. The following usages are possible : - If you have a genomic full reference sequence and an annotation file (gtf or gff), use
                        'vizitig annotate --genome path_to_genome --metadata path_to_annotation_file'. - If you have exons or transcripts reference sequences, use 'vizitig
                        annotate --exons path_to_exon_sequences'. Replace 'exons' by 'transcript' if you have transcripts sequences. With the later feature, you can also add --metadata
                        path_to_annotation_file if you have an annotation file that corresponds to the exons or transcripts reference sequence, but it is not mandatory. What it does : -
                        For the genomic sequence and the annotation file, Vizitig will sort and ingest all the metadata in the annotation file and read the reference sequence using a
                        reading frame. Everytime the whole sequence of a metadata has been read, it will tag the graph with the corresponding metadata. - For the exons or transcripts
                        reference sequence, it will tag the graph with the a generic metadata that has the header of the reference sequence and later add the additional data of the
                        annotation file. The later is therefore optional
    build               build a new graph from BCALM file
    run                 run Vizitig locally

options:
  -h, --help            show this help message and exit

```

Each subcommand has its own help. 

## Environnement variables

It is possible to use environnement variables to change the global
behavor of vizitig:

- VIZITIG_DEFAULT_INDEX: set the default index type choosen among SQLiteIndex or RustIndex (the default)
- VIZITIG_DIR: set the main data directory of vizitig (default is in ~/.vizitig).
- VIZITIG_NO_PARALLEL_INDEX: if set, do not build the index using python multiprocessing (default False for linux and True for the rest).
- VIZITIG_NO_TMP_INDEX: if set, will not use temporary index when performing some annotation operation 
- VIZITIG_PROC_NUMBER:  the number of subprocess used in index building.
- VIZITIG_PYTHON_ONLY: if set to any value, do not use vizibridge (compiled binaries).
- VIZITIG_TMP_DIR: set the temporary data directory of vizitig (default to the choice of tempfile standard module on the system).
- VIZITIG_WORK_MEM: the maximal size of a shard (but could be use for other part of the code).

To change the value of one of those variables, use `export`command. Note that the variable will be changed once, but will go back to defaut if you close the virtual environment. 

```bash
export VIZITIG_PYTHON_ONLY=False
```


# Client based interaction

To launch the web client use the following command in the venv.

```
vizitig run
```

It will open the webclient.

To build a new graph to the application run (still within the venv)

```
vizitig build /path/to/some/bcalm/file
```

with k being the size of the kmers. We recommand using k = 21. The compiled version will work any k < 64.
Beyond this, only specific values of k are available : 113, 127, 239, 241, 251, 255, 487, 491, 499, 509, 511, 1021, 1023. 

You can find those values in the AvailableKmerSize variable of vizitig.types. 

Example of vizitig build commands : 

```
vizitig build my_bcalm.fa 
```

or 

```
vizitig build my_bcalm.fa  --k 21 -n mini_bcalm #mini_bcalm will be the name of the graph 
```

It can take some time and some space on the disk (but should not use too much memory).

To get some information about already created graphs, simply run

```
vizitig info
```

## The vizitig query language

While in the web user interface, a query field is available. Two execution modes are available for the queries. After typing a query, you can : 
- Execute this query on the graph. To do so, click on the "Fetch nodes" green buttons. This will fetch all the corresponding nodes from the database to the user interface (from the disk to the RAM) and materialise the nodes in the user interface.
- Execute this query on the loaded nodes. To do so, click on the "Add filter" blue button, name your filter and add it. Now, in any visualisation instance, you can click on "Add action" and select your filter. This action will only apply to loaded nodes. If you load new nodes, the actions will be applied to them. 

In the CLI (command-line interface), only the first mode is available. Instead of materialising the nodes, the CLI will return a list of nodes IDs. 

The query language is really simple. It contains 3 operators : AND, OR and NOT. Those are logical operators that correspond to conjunction, disjunction, and complement. Their meaning may diverge from what we expect in the current language. We suggest you look at [this page](https://en.wikipedia.org/wiki/Boolean_algebra) if you are not familiar with the concepts of mathematical logic. The Venn diagramm in the section "Diagrammatic representations" sums things up nicely enough. 

Operators can be used between or in front of formulas. In our case, formulas are composed of the name of the metadata (see the section annotations for more details on annotation) you want to query plus its name in parenthesis.

Query for all the nodes that are tagged with the gene DRA_012 : 
```
Gene(DRA_012)
```

Query for all the nodes that are not tagged with this metadata : 
```
NOT Gene(DRA_012)
```

Query for the nodes in the sample 1 or in the sample 2 : 
```
Color(sample1) OR Color(sample2)
```

Query for the nodes in the sample 1 and in the sample 2 (here nodes have to be shared by the 2 samples):
```
Color(sample1) AND Color(sample2)
```

Parenthesis can be used in the process. Query blocs in parenthese will work just like a classic metadata query. 
For instance, if you want all the nodes that are in the sample 1 or in the sample 2 but not in the sample 3 : 

```
(Color(sample1) OR Color(sample2)) AND NOT Color(sample3)
```

Knowing what to type to find a precise metadata may be complicated if you have tricky data, so we built a metadata explorer that you can open in the visualisation by clicking the blue metadata button. First, choose the type of metadata that you want to see and then click on the line corresponding to this metadata. It will add the right query for it in the query field. All that remains to be done is typing the logical operators and the parenthesis to have a functionnal query. 

More details can be found in (doc/query.md).

# Graph Annotations

To color a graph (that is to mark some node of the graph with some metadata)
you can use the `color` subcommand. This command is thought to allow users to keep track of the origin sample of one data. It differs from the other annotation features that we explain below, because it only requires a reference sequence and no annotation data.

We advise you to use the a graph file as input for this command, eventough a classic fasta or fna file will generally work as well. 

If you want to add abundances to the graph, use the --abundances parameter of the color command. In this case, provide a BCALM file. It needs to have the default parameters with regards to abundance in BCALM (no special formatting and no --all-abundance-counts). 

The recommended workflow is the following:

- Build a graph with all your sequences. You can easily build the DBG graph of several sequences using [ggcat](https://github.com/algbio/ggcat) or [BCALM](https://github.com/GATB/bcalm). 
- Use Vizitig build to ingest the graph in Vizitig. 
- Use Vizitig color with your initial sequences (or their graph) to keep track of the origin sample or each sequence. 
- Use vizitig annotate to add annotations using gtf or gff files and reference sequences. You can also provide transcripts or exons sequences alone or with annotations.  

```bash
vizitig color -h
```

```bash
usage: vizitig  [-h] -m name [-d description] [-k file [file ...]] [-b buffer] [-u url [url ...]] [-c color] graph

positional arguments:
  graph                 A graph name. List possible graph with python3 -m vizitig info

options:
  -h, --help            show this help message and exit
  -m name, --metadata-name name
                        A key to identify the metadata to add to the graph
  -d description, --metadata-description description
                        A description of the metadata
  -k file [file ...], --kmer-files file [file ...]
                        Path toward files containing kmers (fasta format)
  -b buffer, --buffer-size buffer
                        Maximum size of a buffer
  -u url [url ...], --kmer-urls url [url ...]
                        URLs toward files containing kmers (fasta format)
  -c color, --color color
                        Default color to use in the vizualisation. Default is None
```

The typical usage would be :

```
vizitig color -k my/awesome/file.fa -d "This contains some cure against the cancer somehow" -m "sample1" my_graph_name
```

After this, you will be able to fetch all the nodes of the graph that correspond to this sample by using the following query :
```
Color(sample1)
```

More complex options exist to add metadata to a graph. One is suited for transcriptomic references, the other for genomic references. 

### Transcript and exon references

To add metadata with transcriptomic or exonic references, use Vizitig annotate. 
```
Vizitig annotate -h 
```

```
usage: vizitig annotate [-h] [-r ref] [-m gtf] [-e exon_sequences] [-t transcript_sequences] graph

positional arguments:
  graph                 A graph name. List possible graph with python3 -m vizitig info

options:
  -h, --help            show this help message and exit
  -r ref, --ref ref     Path toward a (possibly compressed) fasta file containing a reference sequence
  -m gtf, --metadata gtf
                        Path towards a (possibly compressed) gtf file containing metadata of a reference sequence
  -e exon_sequences, --exons exon_sequences
                        Path towards a fasta file containing exon reference sequences
  -t transcript_sequences, --transcripts transcript_sequences
                        Path towards a fasta file containing transcript reference sequences

```

The typical usage would be : 

```
vizitig annotate -t my_data/transcript_ref.fa -m my_data/transcript_annot.gtf my_graph
```

Vizitig will proceed with the following :

-If metadata and reference sequence provided : 
    Vizitig will look for each metadata line found in transcript_annot.gtf, it will look for a reference transcript or gene in the transcript_ref.fa file. If found, it will tag all the nodes that correspond to the reference sequence with the metadata. 
-If transcript or exon references are provided alone, every sequence will be added. Note that for exons, they will be named Exon1, Exon2, ... ExonN. Transcripts will be named after their name in the reference sequence. 

Note : The parser are made for NCBI data. Contact the developpers if you need a specific parser. 

If your gtf files contains a Transcript with id NM_010111, you can query the corresponding nodes with the query : 

```
Transcript(NM_010111)
```

Otherwise you can always use the metadata explorer in the web interface to see how your metadata were formatted. 

### Genomic
To add metadata with genomic references, use Vizitig annotate. 
```
Vizitig annotate -h 
```

```
usage: vizitig annotate [-h] -g genome -m gtf [-p] graph

positional arguments:
  graph                 A graph name. List possible graph with python3 -m vizitig info

options:
  -h, --help            show this help message and exit
  -g genome, --ref-seq genome
                        Path toward a (possibly compressed) fasta files containing reference sequences
  -m gtf, --metadata gtf
                        Path towards a (possibly compressed) gtf files containing metadata of reference sequences
```

The typical usage would be : 
```
vizitig annotate -g my_data/genome_ref.fa -m my_data/annot.gtf my_graph
```

Vizitig will proceed with the following : for each metadata line found in annot.gtf, it will look for the sequence in the reference file. When found, it will tag all the nodes that correspond to the reference sequence with the metadata. Note that it will read the reference sequence sequentially and will need to load the reading frame in RAM (max 2.5 Mo). If you happen to treat genomic references larger than 3 million bases per gene (maybe in plants), contact the developpers. 

If your gtf files contains a Exon with id DRA_0172, you can query the corresponding nodes with the query : 
```
Exon(DRA_0172)
```


## Running a small example

Vizitig comes with a set of data that can be used to explore the tool.
By default, the `mini_bcalm.fa` is available. It is a minimal subset of a human gene. 

To use this example, go in your vizitig folder using a command line tool, activate the venv and run vizitig.

Assuming your vizitig folder is situated in your home folder and you opened a terminal in your home folder (otherwise change the path), you can run: 

```
cd vizitig 
```

to go in your vizitig folder. 

Then: 

```
source venv/bin/activate
```

will activate the venv (virtual environment) to allow vizitig and all its dependencies to run. 

Then: 

```
make small_ex
```

will build the graph, color it with origin sequences and add the gene annotations. This command calls the small_ex part of the Makefile file, that executes the build, color and genes commands. 

To use vizitig, you can finally run 

```
vizitig run
```

A web application will open and you can select the mini_bcalm graph. You can select the genes, or the transcripts that you want to display to have a targeted visualisation.

In any case, as soon as a graph node is displayed, you can unfold every neighbor node from the currently displayed nodes. 

## Removing graphs 
You can delete a graph from the web interface, but also in command line : 

With the venv activated and in the vizitig folder, you can remove a graph by using the following command:

```bash
vizitig rm graph_name
```

For instance, deleting the mini_bcalm.fa graph would require the following line:
```
make rm mini_bcalm
```


## Running a coloring example using fasta data - covid example

This sections aims at giving the users the possibility to build an exemple by themselves from A to Z. We provide the data. 

To run this example, you will need to download the following files :
[click here](https://zenodo.org/records/11192088?token=eyJhbGciOiJIUzUxMiJ9.eyJpZCI6ImJhZWY4Zjk4LTAxNmItNDkzMi05YmMxLTFlZjQ0MDdkYzRhMiIsImRhdGEiOnt9LCJyYW5kb20iOiI3MGU3MWJhOWZhNWZhYzcxZTc3OGU2MDg1ZDc5ZjIxNCJ9.i9wGjOBGVEiuc8F7U65lvhRgLHF4a9zsfjzj8fimP_cT8HK4_Mds_ZBSGeyLtJkF9WkNHV6jW7rgz5JUUGPEZQ).

Please note that we do not claim owernship of the data, nor the relevance of the data naming. 
This data set was created for the purpose of showing a small existing example only. 

You can also conduct the same process with your own files. 

We will build a new graph from four fasta file. In our cases, they are named:

- SARS_CoV_alpha.fna
- SARS_CoV_beta.fna
- SARS_CoV_Spike_alpha.fna
- SARS_CoV_Spike_beta.fna

This dataset is composed of alpha and beta covid, as well as their associated spike proteins. 

Open a terminal in the vizitig folder.

1. Build a graph with our files\
The first step is to build a bcalm graph. We advise to use [ggcat](https://github.com/algbio/ggcat). The following command takes as input the fasta files.


```
ggcat build data/covid/SARS_CoV_* -e -s 1 --kmer-length 21 -o data/covid_example
```

The "SARS_CoV_*"  parameter means "all files that start by SARS_CoV_", in our case all the files (because we named them accordingly). 


The ```-e``` and ```-s``` parameters are really important, as they allow ggcat to build the edges of our graph.

2. Launch the vizitig environement.
*Make sure to be in the parent folder of the vizitig and data folder with your command line tool.*
```
source vizitig/venv/bin/activate
cd vizitig
```

3. Ingest the graph inside vizitig

```
vizitig build ../data/covid_example -n covid_example
```

3. Build the index for the graph 

```
vizitig index build covid_example
```

5. Color the graph with the genomes

We color the graph with the initial sequences. Therefore the graph will be tagged with 4 colors, and we will be able to see the origin sequence of each node. 

```
vizitig color -k ../data/covid/SARS_CoV_alpha.fna -m "Covid_Alpha" covid_example
vizitig color -k ../data/covid/SARS_CoV_beta.fna -m "Covid_Beta" covid_example
vizitig color -k ../data/covid/SARS_CoV_Spike_alpha.fna -m "Spike_Protein_Alpha" covid_example
vizitig color -k ../data/covid/SARS_CoV_Spike_beta.fna -m "Spike_Protein_Beta" covid_example
```


6. Launch vizitig

```
vizitig run
cd ../
```

7. Use vizitig

You can now select your graph "example_covid" on the top-left part. You can search for a specific sub-sequence of kmer and unfold the graph. Several visualisation types are opened by default. You can reopen them using the visualisation menu. 

# Visual operations on graphs 

Once data is loaded in the visualisation part of Vizitig, users can apply visual transformations to this data. This is done by using filters and actions. 

## Filters 

Filters allow users to save a query in the front, and then to apply a visual transformation. The green button "Add as filter" adds the currently written query as a filter. A dropbox opens where users can set a name for their filter. 

The blue button "Filter" opens a filter manager, that exposes the currently existing filters and their associated queries, and allows to delete existing filters.

Filters are saved in the graph. In the case of an exchange of graph between users, the filters are kept. 

Several filters are available by defaut : 
-All : selects all nodes 
-Partial : selects the neighbors of loaded nodes 
-Tips : selects the nodes that have only one neighbor 
-Self loop : selects the nodes that have an edge with themselves
-Selection : all the selected nodes at a given time
-Dynamic selection : all the currently selected nodes

Note that the dynamic selection filter is dynamic, and will change on new selection. 

When using classic selection, you can type "Selection" in the query field to export the current selection as a list of nodes. Users can then create a filter that saves this list of nodes. 

## Actions 

Actions are used to apply visual transformation to the data. 
An action is always associated to a filter. If users do not want to filter nodes and apply transformation on the whole graph, they can use the "All" filter. 

Available actions depend on the type of visualisation users currently work with.

Actions are self-explanatory, except for a few of them :

-Sashimi (for simple graph) or Sashimi Line (for band graph): allows to display the abundance associated to a given color. It is asked that users inputs a color in the "Abundance from" field. The color has to exists in the graph and has abundance associated to it. Beware that the color in the graph is not the same as the color selected for the visual transformation. 
-Center : recenters the user view on the barycenter, but applies no other transformation. 

# Vizitig as librairy and python command line interface

Most of graph operation are directly accessible directly with a Python. It is a thin wrapper
around `NetworkDisk` which is `NetworkX` on disk implementation, storing graphs in a normalized way into a database.

```python
from vizitig import info as vizinfo
L = vizinfo.graphs_list() # get the list of available graph
d = vizinfo.graph_info(L[0]) # return a dict with information about the graph
G = vizinfo.get_graph(L[0]) # get the networkdisk graph
```

You can also get a graph directely by its name. You cannot give a name to your vizitig graph when you build it yet (the name of the ggcat or BCALM file graph will be taken by default) but you can see all the names of the graphs by running 
```
vizitig info
```
in the venv.
If you know the name of your graph, you can also access it using the following method: 

```python
from vizitig import *
G = get_graph('name_of_your_graph') #name of the graph without extension
```

For the mini bcalm graph provided in vizitig, it would be: 
```python
from vizitig import *
G = get_graph('mini_bcalm') #the extension is .db
```

Metadata are stored within the Graph data and are also accessible:

```python
GM = G.metadata # the description and list of all metadata
GM.color_list # list of all the sequences your colored your graph with
```

To save space in the graph, nodes labeled by the metadata contain
the key `i`. For instance:

```python
G.find_all_nodes(0) # return all the nodes tagged with G.graph["meta_list"][0]
```

You can also search for a precise kmer as follows:

```python
G.find_one_node("GCTGCT...ACGT")
```

Or you can fetch all nodes that contains a subsequence as follows:

```
G.find_all_node(seq=lambda e:e.like("%TGCAGCAC%"))
```

The last one will perform a sequential scan over the database as it is not indexed,
so it will be rather slow. All the other query are performed with an appropriate
index accelerating them.
This means that searching for a kmer is way faster than searching by a sequence. 

## Compatibility with NetworkX 

Networkdisk, the package on which vizitig relies, is the standard package in python to manipulate graph. Therefore, any vizitig graph can use the algorithms provided by NetworkX. 
There tons of algorithms available [in NetworkX](https://networkx.org/documentation/stable/reference/algorithms/index.html). Here is a quick example : 

```python
from networkx import diameter
from vizitig.info import get_graph 

G = get_graph("mini_bcalm")
diameter(G)
>>> 34
```

Note that NetworkX functions are functions that take the graph as argument, and not methods. 


## Compiled binary included

Some part of `Vizitig` are compiled and packaged through the `vizibridge`
module.  This module can be toggle off and backtracked to a pure Python
implementation by setting up the environnement variable VIZITIG_PYTHON_ONLY` to
any non empty value.  Part of the optimizations provided by vizibridge are the
sequence computations (for instance the enumeration of the kmers of a
sequence). The performances improvement are considerable on middle to high
sized graph but are limited to Linux with x86_64 machine for now.


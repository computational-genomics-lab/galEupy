
# galEupy
Python module for GAL. It does data processing.
 
## Installation
### For latest pip version
```commandline
pip install galEupy
```

### For latest development version

```batch
git clone https://github.com/computational-genomics-lab/galEupy.git
cd galEupy
pip install .
```

## Usage
```batch
galEupy --help
```

```batch
Welcome to galEupy
usage: galEupy [-h] [-db DBCONFIG] [-path PATHCONFIG] [-org ORGCONFIG] [-upload {all,centraldogma,proteinannotation}] [-info [INFO]] [-org_info [ORG_INFO]]
               [-remove_org [REMOVE_ORG]] [-remove_db [REMOVE_DB]] [-v {none,debug,info,warning,error,d,e,i,w}] [-log LOG_FILE]

optional arguments:
  -h, --help            show this help message and exit
  -db DBCONFIG, --dbconfig DBCONFIG
                        Database configuration file name
  -path PATHCONFIG, --pathconfig PATHCONFIG
                        path configuration file name
  -org ORGCONFIG, --orgconfig ORGCONFIG
                        Organism configuration file name
  -upload {all,centraldogma,proteinannotation}, --upload {all,centraldogma,proteinannotation}
                        Upload data using different levels
  -info [INFO], --info [INFO]
                        Gives information of the table status
  -org_info [ORG_INFO], --org_info [ORG_INFO]
                        Gives information of an organism's upload status
  -remove_org [REMOVE_ORG], --remove_org [REMOVE_ORG]
                        Removes an organism details from the database
  -remove_db [REMOVE_DB], --remove_db [REMOVE_DB]
                        Removes the entire GAL related databases
  -v {none,debug,info,warning,error,d,e,i,w}, --verbose {none,debug,info,warning,error,d,e,i,w}
                        verbose level: debug, info (default), warning, error
  -log LOG_FILE, --log_file LOG_FILE
                        log file

```

### Upload Genome data
Usage to upload a genome
```commandline
galEupy -db <db_configuration_file> -org <organism_configuration_file> -path <path_configuration_file> -v d -upload All
```
Both database and organism configuration files are required to upload the genome. Configuration files are in ini format. 

#### Format for database configuration file

```commandline
[dbconnection]
db_username : 
db_password : 
host : 
db_name : 
port:
```
#### Format for organism configuration file
The version denotes the different strains of the same species if they are available. So in the configuration file, the first strain to be uploaded has version: 1, the second strain has version: 2 and so on. 
If the user has different assemblies of the same strain, they can specify the following using "assembly_version:". 

```commandline
[OrganismDetails]
Organism:
version: 1
source_url:

[SequenceType]
SequenceType: chromosome
scaffold_prefix:

[filePath]
FASTA:
GFF:
eggnog: 
```

### View GAL database log
Usage:
```commandline
galEupy -v d -db <db_configuration_file> -info
```

### Remove an organism from gal database
Usage
```commandline
galEupy -v d -db <db_configuration_file> -org <organism_configuration_file> -remove_org
```
Here, it finds the organism details for the organism configuration file and then deletes the records related it.

### Remove entire GAL related databases
Usage
```commandline
galEupy -v d -db <db_configuration_file> -remove_db
```

## Uploading multiple organisms 

A pipeline written in bash has been added in the current directory, where this README.md file exists. 

The bash script loops through all the genomic fasta (.fna) files and uploads the genomic fasta file as well as the corresponding gff3 files and eggnog emapper annotation files; and uploads this data into the MYSQL database (which has been specified in the database.ini file) using galEupy which has just been installed in the system. 

### test_dataset
Currently the genomic files are hosted in a Google Drive link (since GitHub does not allow a user to host files larger than 25MB): 
[click here to download the files](https://drive.google.com/file/d/12aGDrdPCmoWGtE1fThxUoC0vVrMH0ens/view?usp=sharing)

The Google Drive link contains a test dataset which can be used to test uploading data by galEupy and subsequently modifying the nextJS web application which will host the uploaded database. 
It contains the following : 
1) configuration files : 
  database.ini : contains the MYSQL username, MYSQL password, database name and the name of the host (either localhost or IP address of the computer)
  web.ini : contains the IP address and port of the web application from which the nextJS web application will be launched. Information about this is added in a later section.                                            
2) genomic files of three isolates of Phytophthora melonis. It includes three types of files:
  genomic fasta files 
  genomic gff3 files
  eggnog emapper annotated files. 

The naming convention followed for the basename of a particular isolate is: first three characters of genus, followed by first three characters of species, an underscore and then the name of the strain. 
For eg, for the isolate Phytophthora melonis strain CJ26, the basename would be Phymel_CJ26.
The corresponding files for this isolate are therefore Phymel_CJ26.fna, Phymel_CJ26_with_product_name.gff3 and Phymel_CJ26_eggnog.emapper.annotations respectively. 

#### Generating eggnog emapper annotation files :
  protein FASTA files were processed by EggNOG-mapper (version : emapper-2.1.4-2-6-g05f27b0) using the EggNOG database v5.0.2 


- To test the pipeline, the "test_datasets.zip" file hosted in the Google Drive link must be extracted in the **current** directory which is "**galEupy**".

- Prepare the configuration files (database.ini and web.ini) in the current directory. Sample config files have been provided in the "test_datasets" directory. You can move them to the current "galEupy" directory and modify them according to the instructions provided in this README.md file. 
- Rename "test_datasets" to "**genomes**". 

### Running uploader pipeline
 A pipeline has been written in bash, called "upload_genomes_pipeline.sh", which is present in this particular directory. It requires the following files for each organism strain :
1) FASTA file : ${basename}.fna
2) GFF file : ${basename}_with_product_name.gff3
3) eggnog file : ${basename}_eggnog.emapper.annotations

The name of the files should follow this convention. The basename can be anything. In the test_dataset, three strains of the organism Phytophthora melonis have been included. 

Usage 
```commandline
bash upload_genomes_pipeline.sh
```
## Running the web application

Finally, after uploading all the genomic data into the MYSQL database specified in the database.ini file, the NextJS web application can be launched directly using another bash pipeline which is also present in this particular directory, where this README.md file is located. 



### Configuration file
A web.ini file has been included in the test_dataset directory. It has the following format :
```commandline
PORT: 
IP_ADDRESS: 
```
The port and IP address of the machine where the NextJS web application will be launched is specified here. 

### Running the web application

A bash pipeline called "modify_nextjs_app.sh" has been created and kept in this particular directory. This clones the NextJS web application which has been created in conjunction with galEupy from the GitHub repository where it has been hosted, makes all the required changes to it and finally launches it on the IP address and the port which has been specified in the web.ini file.

#### Pre-requisite software 
To run the web application, there are some third party software which needs to be installed in the system.
 1) Latest versions of node and npm. In the test server these versions were v19.6.1 and 9.4.0 respectively.
 2) For visualisation : JBrowse CLI, samtools and gt must be installed
    These are all installed by the "modify_nextjs_app.sh" bash pipeline. The user has to provide the sudo password as some of this software will be installed globally in the user's system.
    
    
#### Usage
```commandline
bash modify_nextjs_app.sh
```

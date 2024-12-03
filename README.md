
# galEupy
Python module for GAL. It does data processing.
 
## Installation
### For latest pip version
```commandline
pip install galEupy
```

### For latest development version
```commandline
pip install git+https://github.com/computational-genomics-lab/galEupy.git
```
or
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

### Upload a Genome data
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

### Running uploader pipeline
 
 A pipeline has been written in bash, called "upload_genomes_pipeline.sh", which is present in this particular directory. It requires the following files for each organism strain :
1) FASTA file : ${basename}.fna
2) GFF file : ${basename}_with_product_name.gff3
3) eggnog file : ${basename}_eggnog.emapper.annotations

The name of the files should follow this convention. The basename can be anything. In the test_dataset, three strains of the organism Phytophthora melonis have been included. 

##test_dataset
In the current directory, where this README.md file is hosted, another directory has been made called test_dataset. 
It includes a README.md file, database and web configuration files; and a link to a zip file containing all the genomic files hosted in  
Google Drive.

The naming convention followed in the test dataset is first three characters of genus, followed by first three characters of species, an underscore and then the name of the strain. For eg, for the isolate Phytophthora melonis strain CJ26, the basename would be Phymel_CJ26.

The corresponding files are therefore Phymel_CJ26.fna, Phymel_CJ26_with_product_name.gff3 and Phymel_CJ26_eggnog.emapper.annotations respectively. 

Usage 
```commandline
./upload_genomes_pipeline.sh
```
To test the pipeline, the genomic files hosted in the test_dataset.zip file must be extracted and kept in this particular directory. 

The bash script loops through all the fna files and uploads the genomic fasta file as well as the corresponding gff3 files and eggnog emapper annotation files using galEupy which has just been installed in the system. 


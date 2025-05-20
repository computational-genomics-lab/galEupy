# galEupy  
**Genomic Analysis and Loading (GAL) Module**  
*A Python tool for batch processing and managing genomic data in MySQL databases*


## Table of Contents
1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Basic Usage](#basic-usage)
4. [Batch Upload Pipeline](#batch-upload-pipeline)
6. [Test Dataset](#test-dataset)
7. [Web Application Setup](#web-application-setup)
8. [Troubleshooting](#troubleshooting)

## Installation <a name="installation"></a>

### Latest Development Version
```bash
git clone https://github.com/computational-genomics-lab/galEupy.git
cd galEupy
pip install .
```
### Verify Installation
```bash
galEupy --help
```
## Configuration <a name="configuration"></a>

### Database Configuration (database.ini)

Create/modify database.ini with MySQL credentials:
```bash
[dbconnection]
db_username = your_username
db_password = your_password
host = localhost
db_name = gal_db
```
### Organism Configuration Template (organism_config_format.ini)
Template for organism uploads:
```bash
[OrganismDetails]
Organism = Genus_species
strain_number = 1

[SequenceType]
SequenceType = chromosome
scaffold_prefix = 

[filePath]
FASTA = path/to/genomes/Org_strain.fna
GFF = path/to/genomes/Org_strain.gff3
eggnog = path/to/genomes/Org_strain.emapper.annotations
```

## Basic Usage <a name="basic-usage"></a>
Use the CLI with -db flag to specify configuration:

| Command | Description |
| -------- | ------- |
| galEupy -db database.ini -org organism_config_format.ini -v d -upload all |Upload Genomic Data|
|galEupy -db database.ini -info	|Check database status|
|galEupy -db database.ini -remove_org	-org organism.ini|Remove specific organism|
|galEupy -db database.ini -remove_db	|WARNING: Wipe entire database|

## Batch upload pipeline <a name="batch-upload-pipeline"></a>
### Automated pipeline
Use the included script for bulk uploads:
```bash
bash upload_genomes_pipeline.sh
```
### FASTA File Requirements
#### 1. FASTA file Header Structure Requirements
**Required Format:** Each FASTA file **must** contain headers with the following structure: 
``` fasta
>ID Genus species [strain <identifier>] [additional information]
```

**Parsing Rules**

| Field | Content | Extraction Method |
|------------|-------|----------|
| 1 |	Sequence ID	| Mandatory |
| 2-3	| Organism (Genus species)	| Mandatory (fields 2 and 3) |
| 4+	| Strain	| strain <value> OR field 4 |

 **Valid Examples**

 1. With explicit strain:
```fasta
>NC_003424.3 Phytophthora melonis strain CJ26 chromosome 1
```
    - Organism: Phytophthora melonis
    - Strain: CJ26

 2. Without "strain" keyword :
   ```fasta
   >NZ_CP015450.1 Bacillus subtilis 168 complete genome
   ```
    - Organism: Bacillus subtilis
    - Strain: 168

**Invalid Examples**
```fasta
>NG_045678 Saccharomyces (missing species)
>LT962581.1 Fusarium scaffold_5 (missing strain)
```
**⚠️ Error Message for Malformed Files:** 
```bash
"Invalid FASTA file format in [filename]: Header does not match expected formats; skipping."
```

#### 2. File Naming Convention
**Pattern:** `<3-letter genus><3-letter species>_<strain>.fna`  
**Example:** `Schpom_972h-.fna` (Schizosaccharomyces pombe strain 972h-)

| Component  | Format          | Extraction Rule                |
|------------|-----------------|---------------------------------|
| Genus      | First 3 letters | First 3 characters of filename |
| Species    | Next 3 letters  | Characters 4-6 of filename     |
| Strain     | Alphanumeric    | After underscore (_)           |

#### Some features of the web application (the genic region visualisation portion) will be non-functional if this naming convention is not followed. 


## Test dataset <a name="test-dataset"></a>
### Download Test Files 
[Zenodo Link](https://doi.org/10.5281/zenodo.15461870)
##### Includes sample data for 7 organisms/
##### the system works for both Refseq gff file format obtained from NCBI as well the funannonate generated gff3 file format. 

### Setup Instructions
- Download all the files from the zenodo link
- Put the zip folder in the galEupy current directory, extract and rename the folder to "genomes"
- Update configuration files with your MySQL credentials

## Web Application Setup <a name="web-application-setup"></a>

### 1. Configuration (web.ini)
```bash
PORT = 3000 # port where web application will be launched
IP_ADDRESS = localhost  # or your server IP
```
### 2. Launch Web App
#### Requires Ubuntu version 20 and above
```bash
bash modify_nextjs_app.sh 
```
### 3. Runtime Requirements
* Node.js ≥ v19.6.1
* npm ≥ v9.4.0
* JBrowse CLI, samtools, and gt (installed automatically)

### Access Application
```bash
cd galEupy_webApplication
npm run dev
```

## Troubleshooting <a name="troubleshooting"></a>

### Common Issues

#### 1. Database Connection Errors:
* Verify MySQL credentials in database.ini
* Ensure MySQL service is running

#### 2. File Upload Failures:
* Confirm strict adherence to naming conventions
* Check relative file paths in configs

#### 3. Web App Dependencies:

* Run with sudo for global package installations
* Check network permissions for IP/port binding

#### **Maintainers:** Computational Genomics Lab
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
 

# galEupy  
**Genomic Analysis and Loading (GAL) Module**  
*A Python tool for batch processing and managing genomic data in MySQL databases*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents
1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Basic Usage](#basic-usage)
4. [Batch Upload Pipeline](#batch-upload-pipeline)
5. [Test Dataset](#test-dataset)
6. [Web Application Integration](#web-application-integration)
7. [Maintenance](#maintenance)

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
eggnog = path/to/genomes/Org_strain_eggnog.emapper.annotations
```

## Basic Usage <a name="basic-usage"></a>
Use the CLI with -db flag to specify configuration:

| Command | Description |
| -------- | ------- |
|galEupy -db database.ini -org organism_config_format.ini -v d -upload all|Upload Genomic Data|
|galEupy -db database.ini -info	|Check database status|
|galEupy -db database.ini -remove_org	-org organism.ini|Remove specific organism|
|galEupy -db database.ini -remove_db	|WARNING: Wipe entire database|

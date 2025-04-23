# galEupy

## Python Module for Genomic Analysis and Loading

*A tool for batch processing and managing genomic data in MySQL databases.*

---

## Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
  - [Database Configuration (`database.ini`)](#database-configuration-databaseini)
  - [Organism Configuration Template (`organism_config_format.ini`)](#organism-configuration-template-organism_config_formatini)
- [Basic Operations](#basic-operations)
- [Batch Upload Pipeline](#batch-upload-pipeline)
  - [Naming Convention](#naming-convention)
  - [Automated Upload](#automated-upload)
  - [Process Flow](#process-flow)
- [Test Dataset](#test-dataset)
- [Web Application Integration](#web-application-integration)
  - [Configuration (`web.ini`)](#configuration-webini)
  - [Launch](#launch)
- [Maintenance](#maintenance)

---

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/computational-genomics-lab/galEupy.git](https://github.com/computational-genomics-lab/galEupy.git)
    cd galEupy
    ```

2.  **Install the module using pip:**
    ```bash
    pip install .
    ```

3.  **Verify installation:**
    Check if the command-line interface is accessible:
    ```bash
    galEupy --help
    ```

---

## Configuration

Configuration is managed through INI files.

### Database Configuration (`database.ini`)

Create or modify the `database.ini` file with your MySQL database credentials:

```ini
[dbconnection]
db_username = your_username
db_password = your_password
host = localhost
db_name = gal_db
Organism Configuration Template (organism_config_format.ini)
Use this INI format template for configuring individual organism uploads. Replace placeholders with actual paths and details.

Ini, TOML

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
Basic Operations
Use the galEupy command-line tool for basic database management tasks. Ensure you provide the path to your database.ini file using the -db flag.

Command	Description
galEupy -db database.ini -info	Check the status of the configured database.
galEupy -db database.ini -remove_org	Remove a specific organism from the database.
galEupy -db database.ini -remove_db	Warning: Wipe the entire database content.

Export to Sheets
Batch Upload Pipeline
Facilitates uploading multiple genomes efficiently.

Naming Convention
Input genome files (FASTA, GFF, EggNOG) should follow a specific naming convention for automated processing:

<3-letter genus><3-letter species>_<strain>.<ext>

Example: Phymel_CJ26.fna (representing Phytophthora melonis strain CJ26)

Automated Upload
Execute the provided shell script to start the batch upload process:

Bash

bash upload_genomes_pipeline.sh
(Note: Ensure the script has execute permissions and necessary configurations are set.)

Process Flow
The upload_genomes_pipeline.sh script typically performs the following:

Validates the file naming convention against the expected format.
Checks if entries for the organism/strain already exist in the database.
Performs sequential uploads using transaction blocks to ensure data integrity (upload succeeds or fails as a whole).
Generates a checksum verification report upon completion to confirm successful data transfer.
Test Dataset
A sample dataset is provided to help you get started and test the pipeline.

(You might want to add a link or instructions here on how to obtain the test dataset)

The test dataset typically includes:

Genomic data (FASTA, GFF) for 3 Phytophthora melonis strains.
Pre-configured INI files (database.ini, organism configs) tailored for the sample data.
Example EggNOG annotation files (e.g., based on v5.0.2).
Web Application Integration
galEupy can potentially integrate with a web application front-end.

Configuration (web.ini)
Configure web application connection details in web.ini:

Ini, TOML

PORT = 3000
IP_ADDRESS = 127.0.0.1
Launch
A script may be provided to assist in setting up or modifying a companion web application (e.g., a Next.js app):

Bash

bash modify_nextjs_app.sh
(Note: Details of the web application and its specific setup requirements should be documented separately.)

Maintenance
Key features related to data integrity and maintenance:

Version Control: MD5 checksums are calculated and stored for all uploaded files to monitor file integrity.
Transaction Safety: Database uploads utilize transaction rollback mechanisms. If any part of an upload fails, the entire transaction is reverted, preventing partially loaded data.
Update Tracking: Mechanisms are in place to track incremental updates (further details may be needed depending on implementation).

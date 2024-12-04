#!/bin/bash

# A pipeline to upload organism data using galEupy to a MySQL backend

version=1
declare -A uploaded_organisms # Associative array to track already uploaded organisms

for file in genomes/*.fna; do
    # Get the base name of the file (without the extension)
    base=$(basename "$file" .fna)

    # Get the header line from the file. This is the name of the organism
    header=$(grep '^>' "$file" | head -n 1)

    # Extract the organism name
    organism_name=$(echo "$header" | awk -F' ' '/>/{print $2, $3}')

    # Extract the strain name
    strain_name=$(echo "$header" | awk -F'strain ' '{print $2}' | awk '{print $1}')

    gff_file="${base}_with_product_name.gff3"
    eggnog_file="${base}_eggnog.emapper.annotations"

    echo "File: $file"
    echo "Base name: $base"
    echo "Organism name: $organism_name"
    echo "Strain name: $strain_name"
    echo "gff file: $gff_file"
    echo "eggnog_file: $eggnog_file"
    echo "-----------------------------"

    # Check if the organism name has been encountered before
    if [[ -n "${uploaded_organisms[$organism_name]}" ]]; then
        # Organism seen before, increment version
        version=$((version + 1))
    else
        # New organism, record it
        uploaded_organisms["$organism_name"]=1
    fi

    # Making the organism.ini configuration file
    cat <<EOF > organism.ini
[OrganismDetails]
Organism: $organism_name
version: $version
source_url:
strain: $strain_name
assembly_version: 1

[SequenceType]
SequenceType: chromosome
scaffold_prefix:

[filePath]
GenBank:



FASTA: $file
GFF: genomes/$gff_file
eggnog: genomes/$eggnog_file

EOF

    # Upload using galEupy
    # It is assumed that a database.ini file is already present in the working directory
    galEupy -db database.ini -org organism.ini -v d -upload All -log $strain.log
done

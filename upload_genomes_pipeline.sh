#!/bin/bash

# A pipeline to upload organism data using galEupy to a MySQL backend

version=1
declare -A uploaded_organisms # Associative array to track already uploaded organisms

#LOOP THROUGH FASTA FILES AND CHECK IF THEY ARE VALID OR NOT
#if they are not valid : skip
#if valid extract the organism name, strain name 

for file in genomes/*.fna; do
    # Get the base name of the file (without the extension)
    base=$(basename "$file" .fna)

    # Get the header line from the file. This is the name of the organism
    header=$(grep '^>' "$file" | head -n 1)

    # Validate if a header exists
    if [ -z "$header" ]; then
        echo "Invalid FASTA file format: No header found in $file; skipping."
        continue
    fi

    # Extract the organism name (using the second and third fields as default format)
    organism_name=$(echo "$header" | awk -F' ' '/>/{print $2, $3}')

    # Detect if the header contains the word "strain"
    if echo "$header" | grep -q "strain"; then
        # Extract the strain name
        strain_name=$(echo "$header" | awk -F'strain ' '{print $2}' | awk '{print $1}')
    else
        # Try extracting the fourth word as the strain name if "strain" is not present
        strain_name=$(echo "$header" | awk '{print $4}')
        
        # Validate the extracted strain name
        if [ -z "$strain_name" ]; then
            echo "Invalid FASTA file format in $file: Header does not match expected formats; skipping."
            continue
        fi
    fi
# ............................END................................................

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
    galEupy -db database.ini -org organism.ini -v d -upload All -log "$strain_name.log"
done

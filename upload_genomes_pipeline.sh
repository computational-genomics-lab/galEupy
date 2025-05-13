#!/bin/bash

# A pipeline to upload organism data using galEupy to a MySQL backend

# Initialize variables
version=1
declare -A uploaded_organisms # Associative array to track already uploaded organisms

# Loop through FASTA files and process each file
for file in genomes/*.fna; do
    # Extract base name of the file (without extension)
    base=$(basename "$file" .fna)

    # Extract the header line (first line starting with ">")
    header=$(grep '^>' "$file" | head -n 1)

    # Validate the header's existence
    if [ -z "$header" ]; then
        echo "Invalid FASTA file format: No header found in $file; skipping."
        continue
    fi

    # Extract organism name (defaulting to second and third fields)
    organism_name=$(echo "$header" | awk -F' ' '/>/{print $2, $3}')

    # Extract strain name based on header content
    if echo "$header" | grep -q "strain"; then
        # Extract strain name after the keyword "strain"
        strain_name=$(echo "$header" | awk -F'strain ' '{print $2}' | awk '{print $1}')
    else
        # Default to the fourth word if "strain" is not present
        strain_name=$(echo "$header" | awk '{print $4}')

        # Validate strain name
        if [ -z "$strain_name" ]; then
            echo "Invalid FASTA file format in $file: Header does not match expected formats; skipping."
            continue
        fi
    fi

    # ===== Handle .gff or .gff3 files =====
    gff_file=""
    # Check for existing GFF files in genomes directory
    for ext in gff gff3; do
        if [[ -f "genomes/${base}.${ext}" ]]; then
            gff_file="genomes/${base}.${ext}"
            break
        fi
    done

    # Exit if no GFF file found
    if [[ -z "$gff_file" ]]; then
        echo "Error: No GFF file found for ${base} (.gff or .gff3); skipping."
        continue
    fi

    # EggNOG file path
    eggnog_file="genomes/${base}.emapper.annotations"

    # Print details for debugging/logging
    echo "Processing File: $file"
    echo "Base Name: $base"
    echo "Organism Name: $organism_name"
    echo "Strain Name: $strain_name"
    echo "GFF File: $gff_file"
    echo "EggNOG File: $eggnog_file"
    echo "-----------------------------"

    # Check if organism has been processed before
    if [[ -n "${uploaded_organisms[$organism_name]}" ]]; then
        # Increment version if organism already exists
        version=$((version + 1))
    else
        # Add new organism to the tracker
        uploaded_organisms["$organism_name"]=1
    fi

    # Create the organism.ini configuration file
    cat <<EOF > organism.ini
[OrganismDetails]
Organism: $organism_name
strain_number: $version
strain: $strain_name
assembly_version: 1

[SequenceType]
SequenceType: chromosome
scaffold_prefix:

[filePath]
GenBank:
FASTA: $file
GFF: $gff_file
eggnog: $eggnog_file
EOF

    # Upload data using galEupy
    # Assumes a database.ini file is present in the working directory
safe_org=${organism_name//[[:space:]]/_}

logfile="${safe_org}_${strain_name}.log"

    galEupy -db database.ini -org organism.ini -v d -upload All -log "$logfile"
done

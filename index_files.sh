#!/bin/bash

# Directory containing the GFF3 files (current directory)
input_dir="genomes"

# Step 1: Process each *_with_product_name.gff3 file
for input_file in "${input_dir}"/*_with_product_name.gff3; do
    # Get the base name of the file (without path and extension)
    base_name=$(basename "${input_file}" _with_product_name.gff3)

    # Index the corresponding FASTA file
    fasta_file="${input_dir}/${base_name}.fna"
    if [[ -f "${fasta_file}" ]]; then
        echo "Indexing ${fasta_file}..."
        samtools faidx "${fasta_file}"
    else
        echo "Warning: ${fasta_file} not found. Skipping FASTA indexing."
    fi

    # Define the output file name with the required naming convention
    output_file="${input_dir}/${base_name}_with_product_name.fixed.gff3"

    # Run the Python script on the current file
    echo "Fixing GFF3 file: ${input_file} -> ${output_file}"
    python3 fix_gff.py "${input_file}" "${output_file}"
done

# Step 2: Process all *fixed.gff3 files for sorting, compression, and indexing
for fixed_gff in "${input_dir}"/*_with_product_name.fixed.gff3; do
    # Ensure the file exists
    if [[ ! -f "${fixed_gff}" ]]; then
        continue
    fi

    # Define the sorted GFF3 file name
    base_name=$(basename "${fixed_gff}" _with_product_name.fixed.gff3)
    sorted_gff="${input_dir}/${base_name}_with_product_name.sorted.gff3"

    # Sort, tidy, and retain IDs using `gt gff3`
    echo "Sorting and tidying ${fixed_gff}..."
    gt gff3 -sortlines -tidy -retainids "${fixed_gff}" > "${sorted_gff}"

    # Compress and index the sorted GFF3 file
    echo "Compressing and indexing ${sorted_gff}..."
    bgzip "${sorted_gff}"
    tabix "${sorted_gff}.gz"
done

echo "All processing completed!"

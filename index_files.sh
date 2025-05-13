#!/bin/bash

input_dir="genomes"

# Step 1: Process each GFF/GFF3 file
for input_file in "${input_dir}"/*.gff3 "${input_dir}"/*.gff; do
    # Skip if no files found
    [ -f "$input_file" ] || continue
    
    # Get base name without any extension
    base_name=$(basename "$input_file")
    base_name="${base_name%.*}"
    
    # Index FASTA
    fasta_file="${input_dir}/${base_name}.fna"
    if [[ -f "$fasta_file" ]]; then
        echo "Indexing $fasta_file..."
        samtools faidx "$fasta_file"
    else
        echo "Warning: $fasta_file not found. Skipping FASTA indexing."
    fi

    # Process GFF
    output_file="${input_dir}/${base_name}.fixed.gff3"
    echo "Fixing GFF3 file: $input_file"
    python3 fix_gff.py "$input_file" "$output_file"
done

# Step 2: Process fixed files and compress directly
for fixed_gff in "${input_dir}"/*.fixed.gff3; do
    [ -f "$fixed_gff" ] || continue
    
    # Get base name and set final output name
    base_name=$(basename "$fixed_gff" .fixed.gff3)
    final_gff="${input_dir}/${base_name}.gff3.gz"
    
    # Process, compress, and index in one pipeline
    echo "Processing $fixed_gff -> $final_gff"
    gt gff3 -sortlines -tidy -retainids "$fixed_gff" | bgzip > "$final_gff"
    tabix "$final_gff"
    
    # Cleanup intermediate file
    rm "$fixed_gff"
done

echo "All processing completed!"

import re
import sys

def fix_gff3_line(line):
    columns = line.strip().split('\t')

    if len(columns) != 9:
        return line

    attributes = columns[-1].strip()
    attributes_dict = {}
    for attribute in attributes.split(';'):
        key_value = attribute.split('=')
        if len(key_value) == 2:
            attributes_dict[key_value[0]] = key_value[1]
        elif len(key_value) > 2:
            key = key_value[0]
            value = '='.join(key_value[1:])
            attributes_dict[key] = value.replace('=', '-')

    # Fix empty name for genes
    if columns[2] == "gene" and 'ID' in attributes_dict and attributes_dict.get('name') == '':
        attributes_dict['name'] = attributes_dict['ID']

    # Fix empty attributes
    attributes_dict = {k: (v if v != '' else 'Unknown') for k, v in attributes_dict.items()}

    # Reconstruct the attributes part
    fixed_attributes = ';'.join(f"{k}={v}" for k, v in attributes_dict.items())
    columns[-1] = fixed_attributes

    # Reconstruct the line
    return '\t'.join(columns)

def main(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        first_line = infile.readline().strip()
        # Add GFF3 version if not present
        if not first_line.startswith("##gff-version"):
            outfile.write("##gff-version 3\n")
        outfile.write(first_line + '\n')

        for line in infile:
            line = line.strip()
            if not line.startswith('#') and line:
                columns = line.split('\t')
                if len(columns) == 9:
                    line = fix_gff3_line(line)
            outfile.write(line + '\n')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 fix_gff.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    main(input_file, output_file)

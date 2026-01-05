#!/bin/bash
set -e

# ================================
# Load NVM and Setup Node v18
# ================================
export NVM_DIR="$HOME/.nvm"

# Install system dependencies for NVM and Node
sudo apt-get update
sudo apt-get install -y --no-install-recommends curl git build-essential

# Install NVM if missing
if [ ! -s "${NVM_DIR}/nvm.sh" ]; then
    echo "Installing NVM..."
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
    # Source NVM immediately
    [ -s "${NVM_DIR}/nvm.sh" ] && \. "${NVM_DIR}/nvm.sh"
fi

# Load NVM
[ -s "${NVM_DIR}/nvm.sh" ] && \. "${NVM_DIR}/nvm.sh"

# Install specific Node version
LTS_VERSION="18.20.6"
if ! nvm list "${LTS_VERSION}" >/dev/null 2>&1; then
    echo "Installing Node ${LTS_VERSION}..."
    nvm install "${LTS_VERSION}"
fi
nvm use "${LTS_VERSION}" --silent

# Verify Node/npm versions
echo "Node version: $(node --version)"
echo "npm version: $(npm --version)"

# ================================
# Setup Web Application Variables
# ================================

# 1. Prompt for user input and set variables
read -p "Enter the directory where the web application should be cloned (default: current working directory): " CUSTOM_PATH
CUSTOM_PATH=${CUSTOM_PATH:-$(pwd)}

REPO_URL="https://github.com/computational-genomics-lab/P_melonis_web_app"
CLONE_DIR="$CUSTOM_PATH/galEupy_webApplication"
WEB_INI_PATH="$(pwd)/web.ini"
DATABASE_INI_PATH="$(pwd)/database.ini"
DATABASE_JS_PATH="$CLONE_DIR/pages/api/database.js"
PACKAGE_JSON_PATH="$CLONE_DIR/package.json"
INDEX_JS_PATH="$CLONE_DIR/pages/index.js"

# 2. Clone the repository (if not already cloned)
if [ ! -d "$CLONE_DIR" ]; then
    echo "Cloning repository into $CLONE_DIR ..."
    git clone "$REPO_URL" "$CLONE_DIR"
fi

# 3. Check for required configuration files
if [ ! -f "$WEB_INI_PATH" ] || [ ! -f "$DATABASE_INI_PATH" ]; then
    echo "Required configuration files (web.ini and/or database.ini) missing."
    exit 1
fi

# ================================
# Parse Configuration Files
# ================================

# Function to parse INI files
parse_ini_file() {
    local file="$1"
    local key="$2"
    awk -F ':+' -v key="$key" '
        BEGIN { value = ""; }
        $1 ~ "^[[:space:]]*" key "[[:space:]]*$" {
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2);
            value = $2;
        }
        END { print value; }
    ' "$file"
}

# Extract configuration from web.ini
PORT=$(parse_ini_file "$WEB_INI_PATH" "PORT")
IP_ADDRESS=$(parse_ini_file "$WEB_INI_PATH" "IP_ADDRESS")
if [ -z "$PORT" ] || [ -z "$IP_ADDRESS" ]; then
    echo "Web configuration missing (PORT or IP_ADDRESS)."
    exit 1
fi

# Extract database credentials from database.ini
DB_USER=$(parse_ini_file "$DATABASE_INI_PATH" "db_username")
DB_PASSWORD=$(parse_ini_file "$DATABASE_INI_PATH" "db_password")
DB_HOST=$(parse_ini_file "$DATABASE_INI_PATH" "host")
DB_NAME=$(parse_ini_file "$DATABASE_INI_PATH" "db_name")
if [[ -z "$DB_USER" || -z "$DB_PASSWORD" || -z "$DB_HOST" || -z "$DB_NAME" ]]; then
    echo "Database configuration missing."
    exit 1
fi

# ================================
# Update Application Configuration Files
# ================================

# 4. Update database.js with database connection details
if [ -f "$DATABASE_JS_PATH" ]; then
    cat > "$DATABASE_JS_PATH" <<EOL
const mysql = require('mysql2');
const pool = mysql.createPool({
    host: "$DB_HOST",
    user: "$DB_USER",
    password: "$DB_PASSWORD",
    database: "$DB_NAME"
});
module.exports = pool;
EOL
else
    echo "database.js not found."
    exit 1
fi

# 5. Update package.json to set the port for Next.js
if [ -f "$PACKAGE_JSON_PATH" ]; then
    sed -i "s/\"dev\": \"next dev -p [0-9]*\"/\"dev\": \"next dev -p $PORT\"/" "$PACKAGE_JSON_PATH"
else
    echo "package.json not found."
    exit 1
fi

# ================================
# Install Dependencies and System Packages
# ================================

# Function to install system packages using the appropriate package manager

# ================================
# Enhanced System Package Installation
# ================================
install_system_packages() {
    echo "Installing required system packages..."
    sudo apt-get update
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
        git \
        tabix \
        genometools \
        samtools \
        ncbi-blast+ \
        python3 \
        python3-pip \
        libssl-dev \
        libbz2-dev \
        zlib1g-dev \
        libncurses5-dev \
        libncursesw5-dev \
        liblzma-dev
}

# Install system packages
install_system_packages

# Install global npm packages required by the application using the NVM-managed Node
npm install -g --force \
    @jbrowse/cli@3.0.0 \
    next@14.1.0 \
    react@18.2.0 \
    react-dom@18.2.0

# ================================
# Prepare Application Data
# ================================

# Generate index files and move them to public directory
bash index_files.sh
cp -r genomes "$CLONE_DIR/public/"

# Prepare JBrowse2 configuration:
# Remove old configuration file if it exists and generate a new one.
rm -f "$CLONE_DIR/pages/components/visualization/config.json"
#bash "$CLONE_DIR/pages/components/visualization/track_adder.sh"


#===================================
#Make config file for galEupy web app
#====================================


for file in $CLONE_DIR/public/genomes/*.fna ; do
        b=`basename $file .fna`
        echo $file, $b
        jbrowse add-assembly $file --load inPlace
        jbrowse add-track $CLONE_DIR/public/genomes/"$b".gff3.gz --load inPlace --assemblyNames $b.fna
         #UNCOMMENT IF U HAVE RXLR FILES
        #jbrowse add-track $CLONE_DIR/public/genomes/"$b"_rxlr.bw --load inPlace --assemblyNames $b.fna

done

ESCAPED_CLONE_DIR=$(printf '%s\n' "$CLONE_DIR" | sed 's/[\/&]/\\&/g')
#this is done to handle the special characters in $CLONE_DIR for sed

# Remove "$CLONE_DIR/public" string from config.json
sed -i "s|${ESCAPED_CLONE_DIR}/public||g" config.json


mv config.json "$CLONE_DIR/pages/components/visualization/"


#=====================================
# Combining Table Generation and BLAST Data Generation
#=====================================

# Create BLAST_DATA directory (if it doesn't already exist)
BLAST_DATA_DIR="$CLONE_DIR/pages/components/BLAST_DATA/BLASTN_DATA"
mkdir -p "$BLAST_DATA_DIR"

# Initialize table data variable
table_data=""

# Change directory to where the .fna files reside
cd "$CLONE_DIR/public/genomes"

# Process each .fna file
for file in *.fna; do
    # Extract the header from the file (first header line)
    header=$(grep '^>' "$file" | head -n 1)
    if [ -z "$header" ]; then
        continue
    fi

    # Extract organism name (assumes the second and third fields in the header)
    # Example header: ">gi|123456|ref|NC_000001.1| Escherichia coli strain K12"
    organism_name=$(echo "$header" | awk -F' ' '/>/{print $2, $3}')

    # Split organism_name into genus and species (assumes first two words)
    genus=$(echo "$organism_name" | awk '{print $1}')
    species=$(echo "$organism_name" | awk '{print $2}')

    # Extract strain name. If "strain" exists in the header, use that; otherwise, use the fourth field.
    if echo "$header" | grep -q "strain"; then
        strain_name=$(echo "$header" | awk -F'strain ' '{print $2}' | awk '{print $1}')
    else
        strain_name=$(echo "$header" | awk '{print $4}')
    fi

    # Get file size and scaffold count
    size=$(du -sh "$file" | awk '{print $1}')
    scaffold_count=$(grep -c "^>" "$file")

    # Append table row for the index.html (or index.js) update
    table_data+="<tr><td><i>$organism_name</i> strain $strain_name</td><td>$scaffold_count</td><td>$size</td></tr>\n"

    # Construct the BLAST database prefix:
    # first two characters of genus, first two characters of species, underscore, strain name, "_v1"
    blast_prefix="$(echo "$genus" | cut -c1-3)$(echo "$species" | cut -c1-2)_${strain_name}_v1"
    echo "Processing $file -> generating BLAST database with prefix $blast_prefix in $BLAST_DATA_DIR"

    # Generate BLAST database using formatdb (or use makeblastdb if using BLAST+)
    formatdb -i "$file" -p F -o T -n "$BLAST_DATA_DIR/$blast_prefix"
done

# Update index.js with the generated table data.
# We assume the table rows are within a <tbody> ... </tbody> block.
sed -z -i 's|<tbody>.*</tbody>|<tbody>'"$table_data"'</tbody>|g' "$INDEX_JS_PATH"

# ================================
# Launch Next.js Application
# ================================

cd "$CLONE_DIR"
npm install
npm run dev

#!/bin/bash

# ========================
# Setup Web Application
# ========================

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
    git clone "$REPO_URL" "$CLONE_DIR"
fi

# 3. Check for required configuration files
if [ ! -f "$WEB_INI_PATH" ] || [ ! -f "$DATABASE_INI_PATH" ]; then
    echo "Required configuration files missing."
    exit 1
fi

# ==========================
# Parse Configuration Files
# ==========================

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
    echo "Web configuration missing."
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

# ==========================
# Update Configuration Files
# ==========================

# 4. Update database.js
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

# 5. Update package.json
if [ -f "$PACKAGE_JSON_PATH" ]; then
    sed -i "s/\"dev\": \"next dev -p [0-9]*\"/\"dev\": \"next dev -p $PORT\"/" "$PACKAGE_JSON_PATH"
else
    echo "package.json not found."
    exit 1
fi

# ========================
# Install Dependencies
# ========================


# Function to install Node.js and npm using NVM
install_node_nvm() {
    # Install NVM (Node Version Manager)
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
    # Load NVM into the current shell session
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    # Install the desired Node.js version
    nvm install 14
    # Set the installed version as default
    nvm alias default 14
}

# Function to install packages using the appropriate package manager
install_packages() {
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y curl tabix genometools samtools ncbi-blast+
    elif command -v yum &> /dev/null; then
        sudo yum install -y epel-release
        sudo yum install -y curl tabix genometools samtools ncbi-blast+
    elif command -v dnf &> /dev/null; then
        sudo dnf install -y curl tabix genometools samtools ncbi-blast+
    elif command -v pacman &> /dev/null; then
        sudo pacman -Syu --noconfirm curl tabix genometools samtools ncbi-blast+
    else
        echo "Unsupported package manager. Please install the required packages manually."
        exit 1
    fi
}

# Install system packages
install_packages

# Install Node.js and npm
install_node_nvm

# Install global npm packages
npm install -g @jbrowse/cli next

# ==========================
# Prepare Application Data
# ==========================

# Generate index files and move them to public directory
bash index_files.sh
cp -r genomes "$CLONE_DIR/public/"

# Prepare JBrowse2 configuration
bash "$CLONE_DIR/pages/components/visualization/track_adder.sh"

# Replace IP address and port in the application
bash "$CLONE_DIR/string_replace.sh" "$CLONE_DIR/pages" "http:\/\/eumicrobedb.org:3001" "http:\/\/$IP_ADDRESS:$PORT"
bash "$CLONE_DIR/string_replace.sh" "$CLONE_DIR/pages" "..\/..\/..\/public" "http:\/\/$IP_ADDRESS:$PORT"

# Generate table data from genome files
table_data=""
for file in "$CLONE_DIR/public/genomes"/*.fna; do
    base=$(basename "$file" .fna)
    header=$(grep '^>' "$file" | head -n 1)
    if [ -z "$header" ]; then continue; fi

    organism_name=$(echo "$header" | awk -F' ' '/>/{print $2, $3}')
    if echo "$header" | grep -q "strain"; then
        strain_name=$(echo "$header" | awk -F'strain ' '{print $2}' | awk '{print $1}')
    else
        strain_name=$(echo "$header" | awk '{print $4}')
    fi

    size=$(du -sh "$file" | awk '{print $1}')
    scaffold_count=$(grep -c "^>" "$file")
    table_data+="<tr><td><i>$organism_name</i> strain $strain_name</td><td>$scaffold_count</td><td>$size</td></tr>\n"
done

# Update index.js with the generated table data
sed -z -i 's|<tbody>.*</tbody>|<tbody>'"$table_data"'</tbody>|g' "$INDEX_JS_PATH"

# ==========================
# Launch Application
# ==========================

cd "$CLONE_DIR"
npm install
npm run dev

echo "Application running at http://$IP_ADDRESS:$PORT"


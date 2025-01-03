#!/bin/bash

# Prompt the user to enter the path for cloning the repository
read -p "Enter the directory where the web application should be cloned (default: current working directory): " CUSTOM_PATH

# Use the current working directory if no path is provided
if [ -z "$CUSTOM_PATH" ]; then
    CUSTOM_PATH=$(pwd)
fi

# Define variables
REPO_URL="https://github.com/computational-genomics-lab/P_melonis_web_app"
CLONE_DIR="$CUSTOM_PATH/galEupy_webApplication"
WEB_INI_PATH="$(pwd)/web.ini"
DATABASE_INI_PATH="$(pwd)/database.ini"
DATABASE_JS_PATH="$CLONE_DIR/pages/api/database.js"
PACKAGE_JSON_PATH="$CLONE_DIR/package.json"

# Clone the repository into the specified directory
if [ ! -d "$CLONE_DIR" ]; then
    echo "Cloning repository to $CLONE_DIR..."
    git clone "$REPO_URL" "$CLONE_DIR"
else
    echo "Repository already cloned at $CLONE_DIR."
fi

# Ensure the web.ini and database.ini files exist in the starting directory
if [ ! -f "$WEB_INI_PATH" ]; then
    echo "Error: $WEB_INI_PATH not found in the initial directory."
    exit 1
fi

if [ ! -f "$DATABASE_INI_PATH" ]; then
    echo "Error: $DATABASE_INI_PATH not found in the initial directory."
    exit 1
fi

# Extract information from web.ini
echo "Reading configuration from $WEB_INI_PATH..."
PORT=$(grep -oP '(?<=^PORT: )\d+' "$WEB_INI_PATH")
IP_ADDRESS=$(grep -oP '(?<=^IP_ADDRESS: ).+' "$WEB_INI_PATH")
if [ -z "$PORT" ] || [ -z "$IP_ADDRESS" ]; then
    echo "Error: Missing PORT or IP_ADDRESS in $WEB_INI_PATH."
    exit 1
fi

# Extract database credentials from database.ini
echo "Reading database configuration from $DATABASE_INI_PATH..."
DB_USER=$(grep -oP '(?<=^db_username : ).+' "$DATABASE_INI_PATH")
DB_PASSWORD=$(grep -oP '(?<=^db_password : ).+' "$DATABASE_INI_PATH")
DB_HOST=$(grep -oP '(?<=^host : ).+' "$DATABASE_INI_PATH")
DB_NAME=$(grep -oP '(?<=^db_name : ).+' "$DATABASE_INI_PATH")
if [[ -z "$DB_USER" || -z "$DB_PASSWORD" || -z "$DB_HOST" || -z "$DB_NAME" ]]; then
    echo "Error: Missing database configuration in $DATABASE_INI_PATH."
    exit 1
fi

# Modify database.js
if [ -f "$DATABASE_JS_PATH" ]; then
    echo "Modifying $DATABASE_JS_PATH..."
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
    echo "$DATABASE_JS_PATH updated successfully."
else
    echo "Error: $DATABASE_JS_PATH not found."
    exit 1
fi

# Modify package.json
if [ -f "$PACKAGE_JSON_PATH" ]; then
    echo "Modifying $PACKAGE_JSON_PATH to set port to $PORT..."
    sed -i "s/\"dev\": \"next dev -p [0-9]*\"/\"dev\": \"next dev -p $PORT\"/" "$PACKAGE_JSON_PATH"
else
    echo "Error: $PACKAGE_JSON_PATH not found."
    exit 1
fi

# Download prerequisite software
sudo n stable  # Node.js
sudo apt install npm
sudo apt install tabix
sudo apt install genometools
sudo apt install samtools  # For indexing GFF and FNA files
npm install -g @jbrowse/cli  # JBrowse2 CLI
sudo apt install ncbi-blast+-legacy  # BLASTable databases

# Create the index files
bash index_files.sh
mv genomes "$CLONE_DIR/public/"

# Prepare the JBrowse2 configuration
bash "$CLONE_DIR/pages/components/visualization/track_adder.sh"

# Replace IP address and port
bash "$CLONE_DIR/string_replace.sh" "$CLONE_DIR/pages" "http:\/\/eumicrobedb.org:3001" "http:\/\/$IP_ADDRESS:$PORT"
bash "$CLONE_DIR/string_replace.sh" "$CLONE_DIR/pages" "..\/..\/..\/public" "http:\/\/$IP_ADDRESS:$PORT"

# Display success message
echo "Modifications completed. Running the app using npm now..."

# Change directory and run the application
cd "$CLONE_DIR"
npm install
npm run dev

echo "App running on $IP_ADDRESS:$PORT"

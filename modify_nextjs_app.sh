#!/bin/bash

# Define variables
REPO_URL="https://github.com/computational-genomics-lab/P_melonis_web_app"
DATABASE_JS_PATH="P_melonis_web_app/pages/api/database.js"
PACKAGE_JSON_PATH="P_melonis_web_app/package.json"
WEB_INI_PATH="web.ini"
CLONE_DIR="P_melonis_web_app"

# Clone the repository
if [ ! -d "$CLONE_DIR" ]; then
    echo "Cloning repository..."
    git clone "$REPO_URL"
else
    echo "Repository already cloned."
fi

# Extract information from web.ini
if [ -f "$WEB_INI_PATH" ]; then
    echo "Reading configuration from $WEB_INI_PATH..."
    PORT=$(grep -oP '(?<=^PORT: )\d+' "$WEB_INI_PATH")
    if [ -z "$PORT" ]; then
        echo "Error: PORT not found in $WEB_INI_PATH."
        exit 1
    fi
    #IP_ADDRESS=$(grep -oP '(?<=^IP_ADDRESS: )\d+' "$WEB_INI_PATH")
     IP_ADDRESS=$(grep -oP '(?<=^IP_ADDRESS: ).+' "$WEB_INI_PATH")

        if [ -z "$IP_ADDRESS" ]; then
        echo "Error: IP Address not found in $WEB_INI_PATH."
        exit 1
    fi
    echo "IP adress : $IP_ADDRESS"
else
    echo "Error: $WEB_INI_PATH not found."
    exit 1
fi

# Database credentials (replace with actual values from galEupy)
DB_HOST="10.10.10.7"
DB_USER="testadmin"
DB_PASSWORD="forinventorydatabase"
DB_NAME="Pmelonis_database"

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

#move the files into the public genome data directory
echo "Creating a genomes directory and transferring all the files into the directory"
#creating the directory
mkdir -p P_melonis_web_app/public/genomes

#moving
for file in *.fna; do
 # Get the base name of the file (without the extension)
 base=$(basename "$file" .fna)
 mv "$base".fna* P_melonis_web_app/public/genomes
 mv "$base"_with_product_name.gff3* P_melonis_web_app/public/genomes
 #mv "$base"_eggnog.emapper.annotations P_melonis_web_app/public/genomes
done

#prepare the config file for jbrowse2 visualisation


#Replace the ip address and the port
#bash P_melonis_web_app/string_replace.sh "./test" "eumicrobedb.org" "http://$IP_ADDRESS:$PORT"
bash P_melonis_web_app/string_replace.sh "P_melonis_web_app/pages" "http:\/\/eumicrobedb.org:3001" "http:\/\/$IP_ADDRESS:$PORT"

#Display success message
echo "Modifications completed. Running the app using npm now ..."

#open the P_melonis directory and launch the web application
cd P_melonis_web_app

npm install

npm run dev

#!/bin/bash

# Define variables
REPO_URL="https://github.com/computational-genomics-lab/P_melonis_web_app"
DATABASE_JS_PATH="P_melonis_web_app/pages/api/database.js"
PACKAGE_JSON_PATH="P_melonis_web_app/package.json"
WEB_INI_PATH="web.ini"
DATABASE_INI_PATH="database.ini"
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

# Extract database credentials from database.ini
if [ -f "$DATABASE_INI_PATH" ]; then
    echo "Reading database configuration from $DATABASE_INI_PATH..."
    DB_USER=$(grep -oP '(?<=^db_username : ).+' "$DATABASE_INI_PATH")
    DB_PASSWORD=$(grep -oP '(?<=^db_password : ).+' "$DATABASE_INI_PATH")
    DB_HOST=$(grep -oP '(?<=^host : ).+' "$DATABASE_INI_PATH")
    DB_NAME=$(grep -oP '(?<=^db_name : ).+' "$DATABASE_INI_PATH")

    if [[ -z "$DB_USER" || -z "$DB_PASSWORD" || -z "$DB_HOST" || -z "$DB_NAME" ]]; then
        echo "Error: Missing database configuration in $DATABASE_INI_PATH."
        exit 1
    fi
else
    echo "Error: $DATABASE_INI_PATH not found."
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


#downloading the pre-requisite software
sudo n stable #node
sudo apt install npm #npm
sudo apt install genometools
sudo apt install samtools #for indexing gff and fna files respectively
npm install -g @jbrowse/cli #for installing cli version of jbrowse2


#creating the index files
bash index_files.sh
#moving
mv genomes P_melonis_web_app/public/

#prepare the config file for jbrowse2 visualisation
bash P_melonis_web_app/pages/components/visualization/track_adder.sh

#Replace the ip address and the port
#bash P_melonis_web_app/string_replace.sh "./test" "eumicrobedb.org" "http://$IP_ADDRESS:$PORT"
bash P_melonis_web_app/string_replace.sh "P_melonis_web_app/pages" "http:\/\/eumicrobedb.org:3001" "http:\/\/$IP_ADDRESS:$PORT"
bash P_melonis_web_app/string_replace.sh "P_melonis_web_app/pages" "..\/..\/..\/public" "http:\/\/$IP_ADDRESS:$PORT"

#Display success message
echo "Modifications completed. Running the app using npm now ..."

#open the P_melonis directory and launch the web application
cd P_melonis_web_app
npm install
npm run dev

echo "App running on $IP_ADDRESS:$PORT"

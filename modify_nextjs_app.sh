#!/bin/bash

REPO_URL="https://github.com/computational-genomics-lab/P_melonis_web_app"
DATABASE_JS_PATH="P_melonis_web_app/pages/api/database.js"
PACKAGE_JSON_PATH="P_melonis_web_app/package.json"
WEB_INI_PATH="web.ini"
CLONE_DIR="P_melonis_web_app"

# Cloning the git repository
if [ ! -d "$CLONE_DIR" ]; then
    echo "Cloning repository..."
    git clone "$REPO_URL"
else
    echo "Repository already cloned."
fi

# Extracting information from web.ini
if [ -f "$WEB_INI_PATH" ]; then
    echo "Reading configuration from $WEB_INI_PATH..."
    PORT=$(grep -oP '(?<=^PORT: )\d+' "$WEB_INI_PATH")
    if [ -z "$PORT" ]; then
        echo "Error: PORT not found in $WEB_INI_PATH."
        exit 1
    fi
else
    echo "Error: $WEB_INI_PATH not found."
    exit 1
fi

# Database credentials 
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

echo "Modifications completed. You can now run the application using npm."

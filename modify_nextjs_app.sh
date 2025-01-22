#!/bin/bash

# 1. Prompt for user input and set variables
read -p "Enter the directory where the web application should be cloned (default: current working directory): " CUSTOM_PATH

if [ -z "$CUSTOM_PATH" ]; then
    CUSTOM_PATH=$(pwd)
fi

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

# 3. Check for required files
if [ ! -f "$WEB_INI_PATH" ]; then exit 1; fi
if [ ! -f "$DATABASE_INI_PATH" ]; then exit 1; fi

# 4. Function to parse INI files
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

# 5. Extract configuration from web.ini
PORT=$(parse_ini_file "$WEB_INI_PATH" "PORT")
IP_ADDRESS=$(parse_ini_file "$WEB_INI_PATH" "IP_ADDRESS")
if [ -z "$PORT" ] || [ -z "$IP_ADDRESS" ]; then exit 1; fi

# 6. Extract database credentials from database.ini
DB_USER=$(parse_ini_file "$DATABASE_INI_PATH" "db_username")
DB_PASSWORD=$(parse_ini_file "$DATABASE_INI_PATH" "db_password")
DB_HOST=$(parse_ini_file "$DATABASE_INI_PATH" "host")
DB_NAME=$(parse_ini_file "$DATABASE_INI_PATH" "db_name")
if [[ -z "$DB_USER" || -z "$DB_PASSWORD" || -z "$DB_HOST" || -z "$DB_NAME" ]]; then exit 1; fi

# 7. Modify database.js
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
    exit 1
fi

# 8. Modify package.json
if [ -f "$PACKAGE_JSON_PATH" ]; then
    sed -i "s/\"dev\": \"next dev -p [0-9]*\"/\"dev\": \"next dev -p $PORT\"/" "$PACKAGE_JSON_PATH"
else
    exit 1
fi

# 9. Configure npm global directory
mkdir -p ~/.npm-global
npm config set prefix '~/.npm-global'
export PATH=~/.npm-global/bin:$PATH
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
source ~/.bashrc

# 10. Install prerequisites
sudo n stable
sudo apt install -y npm
sudo apt install -y tabix
sudo apt install -y genometools
sudo apt install -y samtools
npm install -g @jbrowse/cli
sudo apt install -y ncbi-blast+-legacy

# 11. Create the index files and move them to the public directory
bash index_files.sh
mv genomes "$CLONE_DIR/public/"

# 12. Prepare the JBrowse2 configuration
bash "$CLONE_DIR/pages/components/visualization/track_adder.sh"

# 13. Replace IP address and port
bash "$CLONE_DIR/string_replace.sh" "$CLONE_DIR/pages" "http:\/\/eumicrobedb.org:3001" "http:\/\/$IP_ADDRESS:$PORT"
bash "$CLONE_DIR/string_replace.sh" "$CLONE_DIR/pages" "..\/..\/..\/public" "http:\/\/$IP_ADDRESS:$PORT"

# 14. Generate table data from genomes directory
table_data=""
for file in $CLONE_DIR/public/genomes/*.fna; do
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

# 15. Modify index.js file
sed -z -i 's|<tbody>.*</tbody>|<tbody>'"$table_data"'</tbody>|g' "$INDEX_JS_PATH"

# 16. Run the application
cd "$CLONE_DIR"
npm install
npm run dev

echo "App running on $IP_ADDRESS:$PORT"

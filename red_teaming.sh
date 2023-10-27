echo "Copying config"
rm -rf src/red_teaming/config_*
mkdir src/red_teaming/config_1
cp -r config/ src/red_teaming/config_1/

echo "Starting server"
nemoguardrails server --config=src/red_teaming --port=8082
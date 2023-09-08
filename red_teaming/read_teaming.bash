echo "Copying config"
rm -rf red_teaming/config_*
mkdir red_teaming/config_1
cp -r config/ red_teaming/config_1/

echo "Starting server"
nemoguardrails server --config=red_teaming --port=8082
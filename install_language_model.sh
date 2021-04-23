source config.py

# shellcheck disable=SC2154
model="${language}_model"
model_name="${language}_model_name"
echo "${!model}"

mkdir -p src/models
cd src/models || exit 2
wget "${!model}"
# shellcheck disable=SC2154
unzip "${!model_name}".zip
mv "${!model_name}" model_"$language"
rm "${!model_name}".zip
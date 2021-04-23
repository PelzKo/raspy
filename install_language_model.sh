DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

source "$DIR"/config.py

# shellcheck disable=SC2154
model="${language}_model"
model_name="${language}_model_name"
#echo "${!model}"

mkdir -p "$DIR"/src/models
cd "$DIR"/src/models || exit 2
wget "${!model}"
unzip "${!model_name}".zip
mv "${!model_name}" model_"$language"
rm "${!model_name}".zip
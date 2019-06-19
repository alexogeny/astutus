sudo apt-get upgrade
sudo apt-get update

sudo apt-get install redis python3.7 libopus git
sudo pip install poetry

git clone https://github.com/lxmcneill/astutus
cd astutus
python -m venv .venv
source .venv
pip install -r requirements.txt

MEPA - Version corrigée OpenAI

Ce ZIP garde le site original et corrige seulement le simulateur de prompts IA.

Commandes Ubuntu / VS Code :

cd ~/Downloads
unzip ia_sensibilisation_openai_fixed.zip
cd ia_sensibilisation

sudo apt update
sudo apt install python3-full python3-venv python3-pip -y

rm -rf venv
python3 -m venv venv
source venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

export OPENAI_API_KEY="TA_CLE_OPENAI"

python app.py

Puis ouvrir :
http://localhost:5000

Important :
- le simulateur IA répond uniquement en texte ;
- si la clé OpenAI n’est pas mise, le site affiche un message explicatif au lieu de faire semblant ;
- l’ancien app.py est sauvegardé dans app_original_backup.py.

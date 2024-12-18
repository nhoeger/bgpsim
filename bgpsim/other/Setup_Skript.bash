#!/bin/bash
# Execute script with sudo rights, to allow all commands to be executed successfully
apt-get update -y
apt install python3-pip -y
pip3 install --user pipenv
export PATH="$PATH:/home/$USER/.local/bin"
apt install git -y
#Replace git clone with link to your repository
#Creation of Personal acces token necessary to clone repository by command line
git clone https://github.com/nhoeger/bgpsim
#Replace with Name of your repository you cloned to cd inside there
cd bgpsim 
#git checkout if necessary as you need to change the branch of the repository
#git checkout #Name of branch
#git pull
pipenv run pip3 list
pipenv run pip3 install click
pipenv run pip3 install networkx
pipenv run pip3 install matplotlib

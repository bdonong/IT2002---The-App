#? Try running this executable with bash (or other sh-like shell of your preference to help you install tools to build the front-end application)
#? Written for linux-based OS's
sudo apt-get install curl
curl https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash

source ~/.bashrc #? change it to your default shell, if you have one. Otherwise, don't

nvm install --latest

source ~/.bashrc #? The same on this line too

npm --version
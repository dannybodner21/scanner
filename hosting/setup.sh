#!/bin/sh

# Install git and python
sudo yum install -y git python pip

# Clone the repo and use the Sprint-1 branch
git clone -b Sprint-1 https://github.com/BoogieHauser/grandmas_recipe_box.git

# Install python packages
pip install -r grandmas_recipe_box/requirements.txt
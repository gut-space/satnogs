#!/bin/sh

# Get rid of any mess that could be in progress
git merge --abort
git cherry-pick --abort

# Discard any local changes and switch to master
git reset --hard

# Disabled for testing. The problem with testing is that if this
# checks out master, then there's no way to test this change on
# a branch. As such, this fill be uncommented only AFTER this
# update procedure is merged to master.
#git checkout master

# This will wipe all non-tracked files. It's a bit much.
#git clean -fxd

# Get the new version
git pull

# Run the installation script
source venv/bin/activate
python setup.py install

# Restart apache
sudo systemctl apache2 restart

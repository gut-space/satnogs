#!/bin/bash

remote_repo_status() {
    UPSTREAM="origin/master"
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse "$UPSTREAM")
    BASE=$(git merge-base @ "$UPSTREAM")

    if [ $LOCAL = $REMOTE ]; then
        # "Up-to-date"
        return 0
    elif [ $LOCAL = $BASE ]; then
        # "Need to pull"
        return 1
    elif [ $REMOTE = $BASE ]; then
        # "Need to push"
        return 2
    else
        # "Diverged"
        return 3
    fi
}

remote_repo_status
repo_status=$?

if (( repo_status == 0)); then
    echo "Repository is up-to-date"
    exit 0
fi
if (( repo_status > 1)); then
    echo "Repository is modified. Reset changes and try again."
    exit 1
fi

git pull
python3 setup.py install
python3 cli.py clear
python3 cli.py plan --force
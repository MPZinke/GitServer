# If user exists and group/repo does not exist
groupadd git-repo-<username>-<repo_name>
usermod -a -G git-repo-<username>-<repo_name> <username>

mkdir /srv/git/<username>/<repo_name>
chgrp git-repo-<username>-<repo_name> /srv/git/<username>/<repo_name>
# From https://gist.github.com/drmalex07/654857322ab390fd557ba8e6047189fd
chmod g+rwxs /srv/git/<username>/<repo_name>

git init --bare --shared=group /srv/git/<username>/<repo_name>

#!/bin/sh
# Use the 'geni-get' tool to obtain an SSH private key and save it to '~/.ssh/id_rsa'.
/usr/bin/geni-get key > ~/.ssh/id_rsa
# Change the permissions of the private key file to make it readable and writable only by the owner.
chmod 600 ~/.ssh/id_rsa
# Generate a public key from the private key and save it to '~/.ssh/id_rsa.pub'.
ssh-keygen -y -f ~/.ssh/id_rsa > ~/.ssh/id_rsa.pub
# Append the content of the public key to the 'authorized_keys' file, allowing the associated private key to authenticate.
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
# Set the permissions on the 'authorized_keys' file to make it readable by the owner and readable by others.
chmod 644 ~/.ssh/authorized_keys
#!/bin/sh

# TODO create table with account, context, cluster
# TODO export AWS_PROFILE env
# TODO should set per session with tmux env?
# TODO sent to every pane

find ~/.kube/ -maxdepth 1 -not -type d -printf "%f\n" \
  | fzf-tmux -p --border --bind 'enter:execute(tmux setenv KUBECONFIG ~/.kube/{1} && clear)+abort' | true

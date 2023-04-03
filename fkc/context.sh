#!/bin/sh

# TODO create table with account, context, cluster
# TODO export AWS_PROFILE env
# TODO should set per session with tmux env?

find ~/.kube/ -maxdepth 1 -not -type d -printf "%f\n" \
  | fzf --bind 'enter:execute(tmux send-keys "tenv KUBECONFIG ~/.kube/{1} && clear" Enter)+abort'

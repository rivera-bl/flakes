#!/bin/sh

# TODO create table with account, context, cluster
# TODO export AWS_PROFILE env

# exit if context is empty
context=$(find ~/.kube/ -maxdepth 1 -not -type d -printf "%f\n" | fzf-tmux -p --border --header "context")

if [ ! -z "${context}" ]; then
  tmux setenv KUBECONFIG ~/.kube/${context}
  tmux list-panes -s -F '#{pane_id} #{pane_current_command}' | grep 'zsh' | cut -d' ' -f1 | xargs -I {} tmux send-keys -t {} "export KUBECONFIG=~/.kube/${context} && clear" Enter
fi

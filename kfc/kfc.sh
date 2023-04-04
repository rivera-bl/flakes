#!/bin/sh

# TODO create table with account, context, cluster

# ejecutar solo si $1 es igual a "context"
if [ "$1" = "context" ]; then
  # get context
  context=$(find ~/.kube/ -maxdepth 1 -not -type d -printf "%f\n" | fzf-tmux -p --border --header "context")

  # if context is not empty
  if [ ! -z "${context}" ]; then
  tmux setenv KUBECONFIG ~/.kube/${context}
  tmux list-panes -s -F '#{pane_id} #{pane_current_command}' \
    | grep 'zsh' | cut -d' ' -f1 | xargs -I {} \
    tmux send-keys -t {} "export KUBECONFIG=~/.kube/${context} && clear" Enter
  fi

# else if $1 is equal to "config" then list clusters
elif [ "$1" = "config" ]; then
  cluster=$(aws eks list-clusters --query 'clusters[*]' --output text | fzf)
  if [ ! -z "${cluster}" ]; then
  aws eks update-kubeconfig \
    --kubeconfig ~/.kube/${cluster} --name ${cluster} --region us-east-1
  fi
fi 

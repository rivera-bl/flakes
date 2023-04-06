#!/bin/sh

# TODO convert into flake, will be useful to install dependencies
# TODO make _tmux_send_env_session a system wide function, create library?
# TODO send ^w zsh function to all panes instead of clear
# TODO rename input vars context and config

set -e
KUBECONFIG_BASEPATH="$HOME/.kube"

function _tmux_send_env_session(){
  tmux setenv $1 $2
  tmux list-panes -s -F '#{pane_id} #{pane_current_command}' \
    | grep 'zsh' | cut -d' ' -f1 | xargs -I {} \
    tmux send-keys -t {} "export $1=$2" Enter C-l
}

function set_awsprofile(){
  # get AWS account from cluster ARN
  ACCOUNT=$(kubectl config view --minify -o jsonpath='{.contexts[].context.cluster}' | \
    cut -d':' -f5)
  [ -z "$ACCOUNT" ] && exit 1
  ROLE=$(grep -m 1 -oP "\[profile ${ACCOUNT}_\K[^]]+" ~/.aws/config)
  _tmux_send_env_session AWS_PROFILE ${ACCOUNT}_${ROLE}
}

function set_context(){
  menu=$(find ~/.kube/ -maxdepth 1 -not -type d -printf "%f\n" \
            | fzf-tmux -p --border --header "context")
  context="$KUBECONFIG_BASEPATH/$menu"
  if [ ! -z "$context" ]; then
    _tmux_send_env_session KUBECONFIG $context
    export KUBECONFIG=$context
    set_awsprofile $context
  fi
}

function add_cluster(){
  sts=$(aws sts get-caller-identity --region us-east-1)
  [ -z "$sts" ] && { fws --login;}

  cluster=$(aws eks list-clusters --query 'clusters[*]' --output text --region us-east-1 \
    | fzf-tmux -p --border --header "cluster")
  if [ ! -z "${cluster}" ]; then
  aws eks update-kubeconfig \
    --kubeconfig ~/.kube/${cluster} --name ${cluster} --region us-east-1
  fi
}

while getopts ":cr" opt; do
  case ${opt} in
    c) set_context;;
    r) add_cluster;;
    \?) echo "Opción inválida: -$OPTARG" >&2; exit 1;;
  esac
done

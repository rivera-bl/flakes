#!/bin/sh

set -e
KUBECONFIG_BASEPATH="$HOME/.kube"

function help_(){
  echo -e "Usage: $0 [-c] [-r] [-h]\n
Options:
  -c\tTmux setenv \$KUBECONFIG to \"~/.kube/\${selection}\". Set \$AWS_PROFILE if EKS cluster 
  -r\tAdd EKS cluster to kubectl config. If no creds call \"fws --login\"
  -h\tShow this help message"
}
[ $# -eq 0 ] && { help_; exit 1; }

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
  sts=$(aws sts get-caller-identity --region us-east-1 2> /dev/null || true)
  [ -z "$sts" ] && { tmux display-popup -b rounded -E 'fws --login'; }
  export AWS_PROFILE=$(tmux showenv AWS_PROFILE | cut -d'=' -f2)

  cluster=$(aws eks list-clusters --query 'clusters[*]' --output text --region us-east-1 \
    | fzf-tmux -p --border --header "cluster")
  if [ ! -z "${cluster}" ]; then
  aws eks update-kubeconfig \
    --kubeconfig ~/.kube/${cluster} --name ${cluster} --region us-east-1
  fi
}

while getopts ":crh" opt; do
  case ${opt} in
    c) set_context;;
    r) add_cluster;;
    h) help_;;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1;;
  esac
done

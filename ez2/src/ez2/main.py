import boto3
import subprocess
import argparse
import csv
import os
import sys

# TODO --bind to get all the policies attached to an instance profile (usually the instance profile name is the same as the role name)
# # aws ec2 describe-instances --instance-ids YOUR_INSTANCE_ID --query 'Reservations[].Instances[].IamInstanceProfile.Arn' --output text
# # aws iam list-attached-role-policies --role-name YOUR_ROLE_NAME
# TODO make readable the sg bind
# # --bind "ctrl-s:execute(aws ec2 describe-security-groups --group-ids $(aws ec2 describe-instances --instance-ids {{1}} --query 'Reservations[].Instances[].SecurityGroups[].GroupId' --output text) | nvim -R -c 'set syntax=json')" \

def get_account_id():
    try:
        sts_client = boto3.client('sts')
        response = sts_client.get_caller_identity()
        account_id = response['Account']
        return account_id
    except Exception as e:
        print(f"Error retrieving account ID: {e}")
        sys.exit()

def list_ec2_instances():
    instances = []
    ec2_client = boto3.client('ec2')

    print("Retrieving EC2 instances...")
    response = ec2_client.describe_instances()
    print("EC2 instances retrieved.")

    for reservation in response['Reservations']:
        for instance in reservation['Instances']:
            if instance['State']['Name'] != 'running':
                continue

            instance_id = instance['InstanceId']
            instance_name = ""
            instance_type = instance['InstanceType']
            image_id = instance['ImageId']
            private_ip = instance['PrivateIpAddress']
            subnet_id = instance['SubnetId']

            for tag in instance['Tags']:
                if tag['Key'] == 'Name':
                    instance_name = tag['Value']
                    break

            launch_time = instance['LaunchTime'].strftime("%Y-%m-%d %H:%M:%S")
            instances.append([instance_id, instance_name, instance_type, image_id, private_ip, subnet_id, launch_time])

    print("Sorting instances by LaunchTime ...")
    sorted_instances = sorted(instances[1:], key=lambda x: x[6], reverse=True)
    sorted_instances.insert(0, ["Instance ID", "Name", "Instance Type", "Image ID", "Private IP", "Subnet ID"])
    print("Instances sorted.")

    # Remove launch_time from the final list
    sorted_instances = [[instance[0], instance[1], instance[2], instance[3], instance[4], instance[5]] for instance in sorted_instances]

    return sorted_instances

def write_csv(csvfile, data):
    if os.path.exists(csvfile):
        os.remove(csvfile)

    os.makedirs(os.path.dirname(csvfile), exist_ok=True)
    with open(csvfile, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)
    print(f"Instances written to {csvfile}.")

def print_columns(data):
    widths = [max(map(len, col)) for col in zip(*data)]
    for row in data:
        print("  ".join((val.ljust(width) for val, width in zip(row, widths))))

def main():
    parser = argparse.ArgumentParser(description='EC2 Instance actions with fzf')
    parser.add_argument('--load', action='store_true', help='Load EC2 instances into a CSV file')
    parser.add_argument('--list', action='store_true', help='List EC2 instances using fzf')
    args = parser.parse_args()

    account = get_account_id()
    cache_path = "/tmp/ec2"
    csvfile = f"{cache_path}/{account}_instances.csv"

    command = f"""cat {csvfile} \
                 | column -t -s, \
                 | fzf --header-lines=1 \
                    --header "| enter:ssm | ctrl-v:describe | ctrl-y:yank | ctrl-space:preview |" \
                    --prompt="{account}>"\
                    --height=80% \
                    --preview-window right,hidden,60% \
                    --preview "aws ec2 describe-instances --instance-ids {{1}} | bat -l json --color always" \
                        --bind "enter:execute(aws ssm start-session --target {{1}})" \
                        --bind "ctrl-v:execute(aws ec2 describe-instances --instance-ids {{1}} | nvim -R -c 'set syntax=json')" \
                        --bind 'ctrl-y:execute-silent(clip.exe <<< {{1}},{{2}},{{3}},{{4}},{{5}},{{6}})' \
                        --bind "ctrl-h:execute-silent(tmux select-pane -L)" \
                        --bind 'ctrl-space:toggle-preview'
                 """

    if not any(args.__dict__.values()):
        parser.print_help()
        exit()


    if args.load:
        if os.path.exists(csvfile):
            print(f"Refreshing cache file {csvfile}.")
        instances = list_ec2_instances()
        write_csv(csvfile, instances)
        subprocess.run(command, shell=True)
    elif args.list:
        if not os.path.exists(csvfile):
            print(f"Cache file {csvfile} not found.")
            instances = list_ec2_instances()
            write_csv(csvfile, instances)
        subprocess.run(command, shell=True)

if __name__ == "__main__":
    main()


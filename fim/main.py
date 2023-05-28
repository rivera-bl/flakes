import boto3
import os
import csv

# TODO set registry as prompt
# TODO --bind pull (ctrl-p, multi)
# TODO --bind show permissions of repository (preview)
# TODO --bind inspect image (ctrl-v)
# TODO --bind copy URI (enter)
# show only repositories
# cat /tmp/fim/images.csv | sed 's/.*\///' | column -t -s, | fzf --header-lines=1

# ---

# TODO print information of the actions it is doing
# TODO use a different name for the local registry with podman, and the ecr registry
region = "us-east-1"
cache_path = "/tmp/fim"

def sizeof_fmt(num, suffix='B'):
    # Adapted from https://stackoverflow.com/a/1094933/6465438
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "{:.1f}{}{}".format(num, unit, suffix)
        num /= 1024.0
    return "{:.1f}{}{}".format(num, 'Yi', suffix)

def list_ecr_images():
    images = []
    session = boto3.Session(region_name=region)
    ecr_client = session.client('ecr')

    response = ecr_client.describe_repositories()

    for repository in response['repositories']:
        repository_name = repository['repositoryName']

        image_response = ecr_client.describe_images(repositoryName=repository_name)

        for image in image_response['imageDetails']:
            if 'imageTags' not in image:
                continue
            image_tags = image['imageTags']
            for tag in image_tags:
                registry = image['registryId'] + "dkr.ecr." + region + ".amazonaws.com/"
                image_tag = registry + repository_name + ":" + tag

                image_pushed_date = image['imagePushedAt'].strftime("%Y-%m-%d %H:%M:%S")
                image_size = image['imageSizeInBytes']

                images.append([image_tag, image_pushed_date, sizeof_fmt(image_size)])
    # Sort in descending order
    sorted_images = sorted(images[1:], key=lambda x: x[1], reverse=True)
    sorted_images.insert(0, ["Image", "Pushed", "Size"])

    # TODO move to another function with csv
    # delete csv if already exists
    csvfile = cache_path + "/images.csv"
    if os.path.exists(csvfile):
        os.remove(csvfile)

    # save as csv
    os.makedirs(cache_path, exist_ok=True)
    with open(csvfile, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(sorted_images)

    # # same as shell 'column -t'
    # # TODO move to another function
    # widths = [max(map(len, col)) for col in zip(*sorted_images)]
    # for row in sorted_images:
    #     print("  ".join((val.ljust(width) for val, width in zip(row, widths))))

if __name__ == "__main__":
    list_ecr_images()


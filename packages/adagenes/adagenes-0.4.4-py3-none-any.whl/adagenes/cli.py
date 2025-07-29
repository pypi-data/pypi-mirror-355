###
# Main script for running AdaGenes from the console
#
# Author: Nadine S. Kurz
#
###
import argparse
import os, subprocess
import yaml
import adagenes.tools.filter_file

def change_file_extension_to_vcf(filename, output_format='vcf'):
    base_name, _ = os.path.splitext(filename)
    new_filename = base_name + '.' + output_format
    return new_filename

def remote_install():
    """
        Script for downloading and installing Onkopus in a restricted environment.
        Downloads all Onkopus images and stores them as .tar files.
        The .tar files can then be uploaded (e.g. in a clinical infrastructure), and loaded using
        'docker load < *.tar'.

        :return:
        """
    __location__ = os.path.realpath(
        os.path.join(os.getcwd(), os.path.dirname(__file__)))
    data_dir = __location__ + "/../conf"
    yml_file_dir = data_dir + '/docker_compose'

    file_list = []
    for root, dirs, files in os.walk(yml_file_dir):
        for file in files:
            file_list.append(os.path.join(root, file))

    # Download all images
    for yml_file in file_list:
        cmd = "docker-compose -f " + yml_file + " pull"
        subprocess.run(cmd, shell=True)

        # Store image as .tar files
        with open(yml_file, 'r') as file:
            data = yaml.full_load(file)

            # print(data)
            services = data.get('services', [])
            # print("Service: ",services)

            for image_key in services.keys():
                image_info = services[image_key]
                image = image_info.get('image')
                container_name = image_info.get('container_name')
                if not image:
                    print("Image name is missing in the YAML file.")
                    continue

            output_file = f"{image.replace('/', '_').replace(':', '_')}.tar"
            with open(output_file, 'wb') as f:
                print("Saving ", container_name, " to ", output_file)
                subprocess.run(['docker', 'save', '-o', output_file, image], check=True)

            print(f"Image '{image}' saved to '{output_file}'")

def main():
    parser = argparse.ArgumentParser(description="Command-line tool for AdaGenes")

    # Add arguments here
    parser.add_argument('action', choices=['annotate', 'filter', 'liftover', 'remote-install'], help='Add an option for the requested action (annotate, filter, liftover)')
    parser.add_argument('-i', '--input_file', default='')
    parser.add_argument('-o', '--output_file', default='')
    parser.add_argument('-g', '--genome_version', default='')
    parser.add_argument('-of', '--output_format', default='')
    parser.add_argument('-f', '--filter', default='')

    args = parser.parse_args()

    input_file = args.input_file
    output_file = args.output_file
    filter_args = args.filter

    if output_file == '':
        output_file = change_file_extension_to_vcf(input_file)

    if args.action == 'annotate':
        pass
    elif args.action == 'filter':
        adagenes.tools.filter_file.filter_file(filter_args, input_file, output_file)
    elif args.action == 'liftover':
        pass
    elif args.action == 'remote-install':
        pass

if __name__ == "__main__":
    main()

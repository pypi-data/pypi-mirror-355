from dataclasses import dataclass

import click
import docker
import os
from datetime import datetime

from dataset_sh import Remote, LocalStorage
from dataset_sh.io import DatasetFileWriter
from dataset_sh.server.core import RepoServerConfig
from dataset_sh.utils.files import checksum
from tests.core.test_io import NameAndCount


def get_default_root_folder():
    """Generate default root folder path with current date."""
    current_date = datetime.now().strftime('%Y_%m_%d')
    return os.path.join('/tmp', 'dataset_sh_sys_testing', f'test_{current_date}')


@dataclass
class DatasetTestingBaseFolder:
    base: str

    @property
    def base_path(self):
        return self.base

    @property
    def server_config(self):
        return os.path.abspath(os.path.join(self.base, 'server.config'))

    @property
    def client_config(self):
        return os.path.abspath(os.path.join(self.base, 'client.config'))

    @property
    def data_dir(self):
        return os.path.abspath(os.path.join(self.base, 'data'))

    @property
    def uploader_dir(self):
        return os.path.abspath(os.path.join(self.base, 'uploader'))

    @property
    def posts_dir(self):
        return os.path.abspath(os.path.join(self.base, 'posts'))

    @property
    def download_dir(self):
        return os.path.abspath(os.path.join(self.base, 'download'))

    @property
    def draft_dir(self):
        return os.path.abspath(os.path.join(self.base, 'drafts'))

    def prepare(self):
        os.makedirs(self.base, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.uploader_dir, exist_ok=True)
        os.makedirs(self.posts_dir, exist_ok=True)
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.draft_dir, exist_ok=True)


def start_server(
        root_folder: DatasetTestingBaseFolder,
        image_name='dsh-dev-local',
        port=29999,
):
    environment = {
        'DSH_APP_HOSTNAME': f'http://localhost:{port}',
    }

    volumes = {
        str(root_folder.data_dir): {
            'bind': '/app/data',
            'mode': 'rw'
        },
        str(root_folder.posts_dir): {
            'bind': '/app/posts',
            'mode': 'rw'
        },
        str(root_folder.uploader_dir): {
            'bind': '/app/uploader',
            'mode': 'rw'
        },
        str(root_folder.server_config): {
            'bind': '/app/dataset-sh-server-config.json',  # exact file path inside container
            'mode': 'ro'  # optional: read-only
        }
    }

    client = docker.from_env()

    try:
        container = client.containers.run(
            image_name,
            name='dsh-test-upload',
            detach=True,
            environment=environment,
            volumes=volumes,
            ports={'8989/tcp': port},
            restart_policy={"Name": "unless-stopped"},
        )

        print(f"Container started: {container.id}")

        # Print container logs
        for line in container.logs(stream=True):
            print(line.decode('utf-8').strip())

    except docker.errors.APIError as e:
        print(f"Error creating container: {e}")
    except docker.errors.ImageNotFound as e:
        print(f"Image not found: {e}")


def run_upload():
    pass


def run_download():
    pass


def is_same_file(f1, f2):
    return checksum(f1) == checksum(f2)


def run_all(root_dir: DatasetTestingBaseFolder):
    """

    1. start server
        1. create config with an user key
        2. mount to config to server container
        3. run container
    2. create draft dataset
    3. upload data to draft dataset
        1. check if data is uploaded
    4. download data from draft dataset
        1. check if data is downloaded

    """
    root_dir.prepare()

    username = 'test-user'
    password = 'test-password'
    host = 'http://localhost:29999'

    # create config with an user key
    repo_config = RepoServerConfig()
    repo_config.update_password(username, password)
    repo_config.allow_upload = True
    repo_config.write_to_file(root_dir.server_config)
    access_key = repo_config.generate_key(username, password)

    start_server(root_dir)

    dataset_file = os.path.join(root_dir.data_dir, 'test-upload.dataset')

    with DatasetFileWriter(dataset_file) as writer:
        writer.add_collection('main', [
            NameAndCount('a', i).to_dict() for i in range(100)
        ])

    version = checksum(dataset_file)

    remote = Remote(host=host, access_key=access_key)
    remote.dataset('test/test-upload').upload_from_file(dataset_file, ['latest'])


    dd = LocalStorage(root_dir.download_dir).dataset('test/test-download')
    remote.dataset('test/test-upload').latest().download_to(dd)


@click.group()
def cli():
    """Dataset.sh CLI tool for managing local development server and data transfer."""
    pass


@cli.command()
@click.option('--image-name', default='dsh37', help='Docker image name')
@click.option('--port', default=29999, type=int, help='Port to run the server on')
@click.option('--root-folder', default=None, help='Root folder for server data')
def server(image_name, port, root_folder):
    """Start the development server."""
    if root_folder is None:
        root_folder = get_default_root_folder()
    start_server(image_name=image_name, port=port, root_folder=root_folder)


@cli.command()
def upload():
    """Upload data to the server."""
    run_upload()


@cli.command()
def download():
    """Download data from the server."""
    run_download()


if __name__ == '__main__':
    cli()

import os
import glob
import json
from collections.abc import MutableSequence
import re
from urllib.parse import urlparse

import yaml
import requests
from cerberus import Validator
from requests.auth import HTTPBasicAuth, AuthBase
from yaml.scanner import ScannerError

from .helpers import fail, success, configure_logger


logger = configure_logger()


class ArrayVariable(MutableSequence):
    """Class to represent an array variable in the pipelines.

    Example:

    >>> env = {
    ...        'EXTRA_ARGS_COUNT': 3,
    ...        'EXTRA_ARGS_0': '--description',
    ...        'EXTRA_ARGS_1': 'text containing spaces',
    ...        'EXTRA_ARGS_2': '--verbose'}
    >>>
    >>> array_variable = ArrayVariable('EXTRA_ARGS', env)
    >>> array_variable[2]
    '--verbose'
    """

    def __init__(self, name, env):
        self._name = name
        self._count = int(env.get(f'{name}_COUNT', '0'))
        self._variables = [env.get(f'{name}_{i}') for i in range(self._count)]

    def __getitem__(self, i):
        return self._variables[i]

    def __setitem__(self, index, value):
        self._variables[index] = value

    def __delitem__(self, index):
        del self._variables[index]

    def insert(self, index, value):
        self._variables.insert(index, value)

    def __len__(self):
        return len(self._variables)

    @classmethod
    def from_list(cls, name, lst):
        array_variable = cls(name, {})
        for var in lst:
            array_variable.append(var)
        return array_variable

    def decompile(self):
        """
        Example

        >>> var = ArrayVariable.from_list('TEST', ['foo','bar', 'baz'])
        >>> var.decompile()
        {'TEST_0': 'foo', 'TEST_1': 'bar', 'TEST_2': 'baz', 'TEST_COUNT': 3}

        """

        dct = {f"{self._name}_{i}": value for i, value in enumerate(self._variables)}
        dct[f"{self._name}_COUNT"] = len(self)
        return dct


class SharedData:
    """This is an interface to the shared pipes data directory.

    Example:

    >>> shared_data = SharedData('/tmp')
    >>> shared_data.get_variable('foo') is None
    True
    >>> shared_data.set_variable('foo', 'bar')
    >>> shared_data.get_variable('foo')
    'bar'
    >>> shared_data.purge()

    Example storing complex data

    >>> shared_data = SharedData('/tmp')
    >>> shared_data.set_variable('my_data', {'my_variable': 'my_value'})
    >>> shared_data.get_variable('my_data')['my_variable']
    'my_value'
    >>> shared_data.purge()
    """

    def __init__(self, path):
        self._path = path
        self._shared_json_file = os.path.join(self._path, '_shared_variables.json')

    def set_variable(self, key, value):
        """Set the shared variable

        Args:
            key (str): Variable key
            value: The value of the variable
        """

        try:
            with open(self._shared_json_file, 'r+') as storage:
                data = json.loads(storage.read())
                data[key] = value
                storage.seek(0)
                storage.truncate()
                json.dump(data, storage)
        except FileNotFoundError:
            with open(self._shared_json_file, 'w+') as storage:
                data = {key: value}
                json.dump(data, storage)

    def get_variable(self, key):
        """Get the value of some variable

        Args:
            key (str): Variable key

        Returns:
            The value of the variable.
        """

        try:
            with open(self._shared_json_file, 'r') as storage:
                data = json.load(storage)
                return data.get(key)
        except FileNotFoundError:
            return None

    def purge(self):
        """
        Purge all shared data
        """

        files = glob.glob(os.path.join(self._path, '_shared_*'))
        for f in files:
            os.remove(f)


class TokenAuth(AuthBase):
    """Attaches auth token to the given Request object."""

    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        # modify and return the request
        r.headers['Authorization'] = 'Bearer ' + self.token
        return r


class Pipe:
    """Base class for all pipes. Provides utilities to work with configuration, validation etc.

    Attributes:
        variables (dict): Dictionary containing the pipes variables.
        schema (dict): Dictionary with the pipe parameters schema in the cerberus format.
        env (dict): Dict-like object containing pipe parameters. This is usually the environment variables that
            you get from os.environ

    Args:
        pipe_metadata (dict): Dictionary containing the pipe metadata
        pipe_metadata_file (str): Path to .yml file with metadata
        schema (dict): Schema for pipe variables.
        validator (cerberus.Validator): cerberus Validator instance

    Pipe variables validation
        Pip variables validation is done at the time of initializing a pipe. The environment variables are
        validated against the schema provided. See https://docs.python-cerberus.org/en/stable/ for more
        details on how to specify schemas.

    """

    def __init__(self, pipe_metadata=None, pipe_metadata_file=None, schema=None,
                 env=None, logger=logger, validator=None, check_for_newer_version=False):
        if pipe_metadata is not None and pipe_metadata_file is not None:
            self.fail(message="Passing both pipe_metadata and pipe_metadata_file is not allowed. "
                              "Please use only one of them.")
        if pipe_metadata_file is not None:
            self.metadata = self.parse_yaml_file(filepath=pipe_metadata_file)
        elif pipe_metadata is not None:
            self.metadata = pipe_metadata
        else:
            self.metadata = {}

        if env is None:
            self.env = os.environ.copy()
        else:
            self.env = env

        self.variables = None
        self.schema = schema
        self.logger = logger
        # validate pipe parameters
        self.validator = validator if validator is not None else Validator(schema=schema, purge_unknown=True)
        self.variables = self.validate()
        self.enable_debug_log_level()
        if check_for_newer_version:
            self.check_for_newer_version()

    def fail(self, message, print_community_link=False):
        """Fail the pipe and exit.

        Args:
            message (str): Error message to show.
            print_community_link (bool): print or not.
        """

        if print_community_link:
            community_link = self.get_community_link()
            community_link_message = f"If you have an issue with the pipe, let us know on Community:{community_link}"
            message = f"{message}\n{community_link_message}"

        fail(message=message)

    @staticmethod
    def success(message, do_exit=False):
        """Show a success message.

        Args:
            message (str): Message to print
            do_exit (bool): Call sys.exit or not

        """

        success(message, do_exit=do_exit)

    def log_info(self, message):
        """Log an info message

        >>> pipe = Pipe(schema={})
        >>> pipe.log_info('hello')

        """

        return self.logger.info(message)

    def log_error(self, message):
        """Log an error message

        >>> pipe = Pipe(schema={})
        >>> pipe.log_error('hello')

        """

        return self.logger.error(message)

    def log_debug(self, message):
        """Log a debug message

        >>> pipe = Pipe(schema={})
        >>> pipe.log_debug('hello')

        """

        return self.logger.debug(message)

    def log_warning(self, message):
        """Log a warning message

        >>> pipe = Pipe(schema={})
        >>> pipe.log_warning('hello')

        """

        return self.logger.warning(message)

    def enable_debug_log_level(self):  # pragma: no cover
        """Enable the DEBUG log level."""

        if self.get_variable('DEBUG'):
            self.logger.setLevel('DEBUG')

    def parse_yaml_file(self, filepath):
        try:
            with open(filepath) as yaml_file:
                content = yaml.safe_load(yaml_file)
        except FileNotFoundError:
            message = f'File {filepath} not found. Please give correct path to file.'
            self.fail(message=message)
        except yaml.YAMLError as exc:
            message = f"Failed to parse {filepath} file: {str(exc)}"
            self.fail(message=message)
        else:
            return content

    def check_for_newer_version(self):
        """Check if a newer version is available and show a warning message

        >>> metadata = {'image': 'bitbucketpipelines/aws-ecs-deploy:0.0.3',
        ...             'repository': 'https://bitbucket.org/atlassian/aws-ecs-deploy'}
        >>> pipe = Pipe(pipe_metadata=metadata, schema={})
        >>> pipe.check_for_newer_version()
        True
        """

        image_string = self.metadata.get('image')
        if image_string is None:
            return False

        pattern = r':((?:[0-9]+\.?){3})(?:@.*$|$)'
        match = next(re.finditer(pattern, image_string), None)
        if match is None:
            self.log_warning(f"Could not parse current version for pipe's image {image_string}")
            return False

        current_version = match.group(1)

        official_pipes_repo = 'https://bitbucket.org/bitbucketpipelines/official-pipes'
        response = requests.get(f"{official_pipes_repo}/raw/master/pipes.prod.json")

        if not response.ok:
            self.log_warning(f'Failed to get the latest pipe version info. Error: {response.text}')
            return False

        repo_url = self.metadata.get('repository')
        repository_path = urlparse(repo_url).path.strip('/')
        released_pipe_info = next((pipe for pipe in response.json() if pipe['repositoryPath'] == repository_path),
                                  {})
        latest_version = released_pipe_info.get('version')
        if not latest_version:
            self.log_warning(f'Could not find released pipe version for {repository_path}. '
                             f'Data matched: {released_pipe_info}')
            return False

        pipe_name = self.get_pipe_name()
        if tuple(map(int, latest_version.split('.'))) > tuple(map(int, current_version.split('.'))):
            self.log_warning(f"New version available: {pipe_name} '{current_version}' to '{latest_version}'")
            return True

    def get_pipe_name(self):
        """Retrive a pipe's name from pipe's repository url.

        >>> metadata = {'image': 'bitbucketpipelines/aws-ecs-deploy:0.0.3',
        ...             'repository': 'https://bitbucket.org/atlassian/aws-ecs-deploy'}
        >>> pipe = Pipe(pipe_metadata=metadata, schema={})
        >>> pipe.get_pipe_name()
        'atlassian/aws-ecs-deploy'
        """

        return urlparse(self.metadata.get('repository')).path[1:]

    def validate(self):
        """Validates the environment variables against a provided schema.

        Variable schema is a dictionary in a cerberus format. See https://docs.python-cerberus.org/en/stable/
        for more details about this library and validation rules.

        """

        if self.schema is None:
            schema = self.metadata['variables']
        else:
            schema = self.schema

        env = {}
        for key, value in self.env.items():
            if key in schema:
                # NOTE: we accept string as this
                if schema[key].get('type', '') == 'string':
                    env[key] = value
                    continue

                try:
                    env[key] = yaml.safe_load(value)
                except ScannerError:
                    # keep a string value
                    env[key] = value

        for key, key_schema in schema.items():
            if key_schema.get('type') == 'list':
                env[key] = ArrayVariable(key, self.env)

        if not self.validator.validate(env):
            self.fail(
                message=f'Validation errors: \n{yaml.dump(self.validator.errors, default_flow_style=False)}')
        validated = self.validator.validated(env)
        return validated

    def get_variable(self, name):
        """Retrieve a pipe variable.

        Args:
            name (str): The name of a variable.

        Returns:
            The value of the variable.
        """

        return self.variables.get(name)

    def get_community_link(self):
        """Retrieve link to create a community question with predefined tags.
        """

        tags = self.metadata.get("tags")
        tags_string = ",".join(tags) if tags else ""
        community_link = f"https://community.atlassian.com/t5/forums/postpage/board-id/bitbucket-pipelines-questions?" \
                         f"add-tags=pipes,{tags_string}"
        return community_link

    def resolve_auth(self):
        """Resolve authorization.
        Currently supported:
        - BITBUCKET_USERNAME and BITBUCKET_APP_PASSWORD
        or
        - BITBUCKET_ACCESS_TOKEN

        Returns
        <HTTPBasicAuth object> or <TokenAuth object>

        Raises
        Authentication missing ... SystemExit: 1

        >>> pipe = Pipe(schema={})
        >>> pipe.resolve_auth()
        Traceback (most recent call last):
        SystemExit: 1

        >>> pipe = Pipe(schema={})
        >>> pipe.variables = {'BITBUCKET_USERNAME': 'test', 'BITBUCKET_APP_PASSWORD': 'test-pass'}
        >>> pipe.resolve_auth() # doctest: +ELLIPSIS
        <...HTTPBasicAuth object at 0x...>

        >>> pipe = Pipe(schema={})
        >>> pipe.variables = {'BITBUCKET_ACCESS_TOKEN': 'test-token'}
        >>> pipe.resolve_auth() # doctest: +ELLIPSIS
        <...TokenAuth object at 0x...>

        """

        username = self.get_variable('BITBUCKET_USERNAME')
        password = self.get_variable('BITBUCKET_APP_PASSWORD')
        token = self.get_variable('BITBUCKET_ACCESS_TOKEN')

        if username and password:
            return HTTPBasicAuth(username, password)
        elif token:
            return TokenAuth(token)
        else:
            self.fail('Authentication missing. You must provide an access token or a username and app password.')

    def run(self):
        """Run the pipe.

        The main entry point for a pipe execution. This will do
        all the setup steps, like enabling debug mode if configure etc.
        """

        self.enable_debug_log_level()

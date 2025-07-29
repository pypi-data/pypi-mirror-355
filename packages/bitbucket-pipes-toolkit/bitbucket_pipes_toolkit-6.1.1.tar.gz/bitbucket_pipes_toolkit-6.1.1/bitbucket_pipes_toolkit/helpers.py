import os
import sys

import colorama
import colorlog
import requests
from colorama import Fore, Style
from requests.adapters import HTTPAdapter, Retry


__all__ = ['configure_logger', 'get_logger', 'get_variable', 'required', 'enable_debug', 'success', 'fail',
           'get_current_pipeline_url', 'divide_chunks', 'BitbucketApiRepositoriesPipelines']

logger = colorlog.getLogger()


def get_logger():
    return logger


def configure_logger():
    """Configure logger to produce colorized output."""

    # Colorlog initialises colorama, however we need to reinit() it to not strip ANSI codes when
    # no tty is attached (i.e inside a docker run in pipes).
    colorama.deinit()
    colorama.init(strip=False)

    # Initialises logging.
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(levelname)s: %(message)s'))
    logger = get_logger()
    logger.addHandler(handler)
    logger.setLevel('INFO')
    colorlog.default_log_colors['INFO'] = 'blue'
    return logger


def get_variable(name, required=False, default=None):
    """Fetch the value of a pipe variable.

    Args:
        name (str): Variable name.
        required (bool, optional): Throw an exception if the env var is unset.
        default (:obj:`str`, optional): Default value if the env var is unset.

    Returns:
        Value of the variable

    Raises
        Exception: If a required variable is missing.
    """

    value = os.getenv(name)
    if required and (value is None or not value.strip()):
        raise Exception('{} variable missing.'.format(name))
    return value if value else default


def required(name):
    """Get the value of a required pipe variable.

    This function is basically an alias to get_variable with the required
        parameter set to True.

    Args:
        name (str): Variable name.

    Returns:
        Value of the variable

    Raises
        Exception: If a required variable is missing.
    """

    return get_variable(name, required=True)


def enable_debug():  # pragma: no cover
    """Enable the debug log level."""

    debug = get_variable('DEBUG', required=False, default="False").lower()
    if debug == 'true':
        logger = get_logger()
        logger.info('Enabling debug mode.')
        logger.setLevel('DEBUG')


def success(message='Success', do_exit=True):
    """Prints the colorized success message (in green)

    Args:
        message (str, optional): Output message
        do_exit (bool, optional): Call sys.exit if set to True

    """

    print('{}✔ {}{}'.format(Fore.GREEN, message, Style.RESET_ALL), flush=True)

    if do_exit:
        sys.exit(0)


def fail(message='Fail!', do_exit=True):
    """Prints the colorized failure message (in red)

    Args:
        message (str, optional): Output message
        do_exit (bool, optional): Call sys.exit if set to True

    """

    print('{}✖ {}{}'.format(Fore.RED, message, Style.RESET_ALL))

    if do_exit:
        sys.exit(1)


def get_current_pipeline_url():
    repo_owner = get_variable('BITBUCKET_REPO_OWNER', required=True)
    repo_slug = get_variable('BITBUCKET_REPO_SLUG', required=True)
    build_number = get_variable('BITBUCKET_BUILD_NUMBER', required=True)
    url = f'https://bitbucket.org/{repo_owner}/{repo_slug}/addon/pipelines/home#!/results/{build_number}'
    return url


def divide_chunks(list_: list, chunk_size: int):
    """Allows to split list by chunk_size chunks"""
    for i in range(0, len(list_), chunk_size):
        yield list_[i:i + chunk_size]


class BitbucketApiRepositoriesPipelines:  # pragma: no cover

    base_url = 'https://api.bitbucket.org/2.0/repositories/'

    def __init__(self, user, password, headers):
        """

        Args:
            user (str): Repository or account variables from Bitbucket
            password (str): Repository or account variables from Bitbucket
            headers (dict): http json header

        """
        self.user = os.getenv(user)
        self.password = os.getenv(password)
        self.headers = headers
        self.base_url = self.base_url

    def get_last_build_number(self, workspace: str, repo_slug: str):
        """ Get last pipeline build number

        Args:
            workspace:
            repo_slug: The repository name

        Returns:
            str: Pipeline build number

        """
        url = self.base_url + f"{workspace}/{repo_slug}/pipelines/"
        request = requests.get(url, auth=(self.user, self.password), headers=self.headers)
        request_value = request.json()
        return request_value['size']

    def get_steps_uuid(self, workspace: str, repo_slug: str, build_number: str):
        """ Get uuid for each step in pipeline

        Args:
            workspace:
            repo_slug: The repository name
            build_number: Particular build number of the pipeline

        Returns:
            dict: Pipeline steps with uuid

        Examples:
            >>> print(steps_uuid) # doctest: +SKIP
            {deploy_with_valid_parameters: '90fsd90fs809gsd90ga9'}

        """
        url = self.base_url + f"{workspace}/{repo_slug}/pipelines/{build_number}/steps/"
        request = requests.get(url, auth=(self.user, self.password), headers=self.headers)
        request_value = request.json()
        steps_uuid = {step['name']: step['uuid'] for step in request_value['values']}
        return steps_uuid

    def get_logs_from_step(self, workspace: str, repo_slug: str, build_number: str, uuid: str) -> str:
        """ Get logs from particular step

        Args:
            workspace:
            repo_slug: The repository name
            build_number: Particular build number of the pipeline
            uuid: The uuid of particular step

        Returns:
            str: Logs from the particular step in pipeline

        """

        url = self.base_url + f'{workspace}/{repo_slug}/pipelines/{build_number}/steps/{uuid}/log'
        request = requests.get(url, auth=(self.user, self.password), headers=self.headers)
        return request.text


class HttpRequestsHandler:
    DEFAULT_MAX_REQUEST_RETRIES = 1
    DEFAULT_REQUEST_BACKOFF_FACTOR = 1
    DEFAULT_MAX_REQUEST_TIMEOUT = 10

    def __init__(self, max_retries=DEFAULT_MAX_REQUEST_RETRIES, backoff_factor=DEFAULT_REQUEST_BACKOFF_FACTOR):
        self.retries = Retry(total=max_retries, backoff_factor=backoff_factor)
        self.http_adapter = HTTPAdapter(max_retries=self.retries)

    def make_session_request(self, method, url, error_base_message="Failed http request.", timeout=DEFAULT_MAX_REQUEST_TIMEOUT, **kwargs):
        try:
            with requests.Session() as s:
                s.mount(prefix='http://', adapter=self.http_adapter)
                s.mount(prefix='https://', adapter=self.http_adapter)
                return s.request(method, url, timeout=timeout, **kwargs)
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout) as e:
            message = f"{error_base_message} Error: {e}"
            fail(message)
        except requests.exceptions.RequestException as e:
            message = f"{error_base_message} Error: {e}"
            fail(message)

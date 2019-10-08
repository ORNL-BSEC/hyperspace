import os
import json
import pathlib
import datetime as dtm
from typing import Optional

from hyperspace.exception import HyperspaceInitializationException
from hyperspace.internal.parser import Parser
from hyperspace.internal.provider import Provider


class Config:
    """
    Read from YAML configuration of a model, specifying all details of the run.
    Is a frontend for the provider, resolving all dependency-injection requests.
    """

    PROJECT_FILE_NAME = '.hyperspace.yaml'
    META_FILE_NAME = 'meta.json'

    @staticmethod
    def find_project_directory(start_path) -> str:
        """ Locate top-level project directory  """
        start_path = os.path.realpath(start_path)
        possible_path = os.path.join(start_path, Config.PROJECT_FILE_NAME)

        if os.path.exists(possible_path):
            return start_path
        else:
            up_path = os.path.realpath(os.path.join(start_path, '..'))
            if os.path.realpath(start_path) == up_path:
                raise RuntimeError(f"Couldn't find project file starting from {start_path}")
            else:
                return Config.find_project_directory(up_path)

    @staticmethod
    def from_project_directory(path) -> str:
        """ Locate given path relative to project directory """
        return os.path.join(Config.find_project_directory('.'), path)

    @classmethod
    def from_file(cls, filename: str, run_number: int = 1, seed: int = None,
                  parameters: Optional[dict] = None, tag: Optional[str] = None):
        """ Alternate constructor to create model config from file """
        with open(filename, 'r') as fp:
            model_config_contents = Parser.parse(fp)

        project_config_path = Config.find_project_directory(os.path.dirname(os.path.abspath(filename)))

        with open(os.path.join(project_config_path, cls.PROJECT_FILE_NAME), 'r') as fp:
            project_config_contents = Parser.parse(fp)

        aggregate_dictionary = {
            **project_config_contents,
            **model_config_contents
        }

        return Config(
            filename=filename,
            configuration=aggregate_dictionary,
            run_number=run_number,
            project_dir=project_config_path,
            seed=seed,
            parameters=parameters,
            tag=tag
        )

    @classmethod
    def script(cls, model_name: str = 'script', configuration: Optional[dict] = None, run_number: int = 1,
               seed: int = None, parameters: Optional[dict] = None, tag: Optional[str] = None):
        """ Create model config from supplied data """
        if configuration is None:
            configuration = {}

        configuration['name'] = model_name

        project_config_path = Config.find_project_directory(os.path.dirname(os.path.abspath(os.getcwd())))

        with open(os.path.join(project_config_path, cls.PROJECT_FILE_NAME), 'r') as fp:
            project_config_contents = Parser.parse(fp)

        aggregate_dictionary = {
            **project_config_contents,
            **configuration
        }

        return Config(
            filename="[script]",
            configuration=aggregate_dictionary,
            run_number=run_number,
            project_dir=project_config_path,
            seed=seed,
            parameters=parameters,
            tag=tag
        )

    def __init__(self, filename: str, configuration: dict, run_number: int, project_dir: str,
                 seed: int = None, parameters: Optional[dict] = None,
                 tag: Optional[str] = None):
        self.filename = filename
        self.run_number = run_number
        self.seed = seed if seed is not None else (dtm.date.today().year + self.run_number)

        self.contents = configuration
        self.project_dir = os.path.normpath(project_dir)

        self.command_descriptors = {
            **self.contents.get('global_commands', {}),
            **self.contents.get('commands', {})
        }

        # This one is special and needs to get removed
        if 'commands' in self.contents:
            del self.contents['commands']

        if 'global_commands' in self.contents:
            del self.contents['global_commands']

        self.provider = Provider(self._prepare_environment(), {'model_config': self}, parameters=parameters)

        if self.provider.has_name('output_directory'):
            self.output_directory_name = self.provider.get("output_directory")
        else:
            self.output_directory_name = 'output'

        self._model_name = self.provider.get("name")

        if self.meta_exists():
            self._meta = self._load_meta()
        else:
            self._tag = tag
            self._meta = None

    def _prepare_environment(self) -> dict:
        """ Return full environment for dependency injection """
        return {**self.contents, 'run_number': self.run_number}

    def _load_meta(self) -> dict:
        """ Load previously written metadata about the project """
        if not self.meta_exists():
            raise HyperspaceInitializationException("Previous run does not exist")

        with open(self.meta_dir(self.META_FILE_NAME), 'rt') as fp:
            return json.load(fp)

    def _create_meta(self) -> dict:
        """ Metadata for this model/config """
        return {
            'run_name': self.run_name,
            'tag': self.tag,
            'created': dtm.datetime.now().strftime("%Y/%m/%d - %H:%M:%S"),
            'config': self.render_configuration()
        }

    def meta_exists(self):
        """ If metadata file exists for this config """
        return os.path.exists(self.meta_dir(self.META_FILE_NAME))

    def enforce_meta(self):
        """ Make sure metadata exists for this config """
        if self._meta is None:
            raise HyperspaceInitializationException("Given model has not been initialized")

    def write_meta(self) -> None:
        """ Write metadata to a file """
        self._meta = self._create_meta()

        pathlib.Path(self.meta_dir()).mkdir(parents=True, exist_ok=True)

        with open(self.meta_dir(self.META_FILE_NAME), 'wt') as fp:
            return json.dump(self.meta, fp)

    def get_command(self, command_name):
        """ Return object for given command """
        return self.provider.instantiate_from_data(self.command_descriptors[command_name])

    def run_command(self, command_name, varargs):
        """ Instantiate model class """
        command_descriptor = self.get_command(command_name)
        return command_descriptor.run(*varargs)

    def project_top_dir(self, *args) -> str:
        """ Project top-level directory """
        return os.path.join(self.project_dir, *args)

    def output_dir(self, *args) -> str:
        """ Directory where to store output """
        return os.path.join(self.project_dir, self.output_directory_name, *args)

    def meta_dir(self, *args) -> str:
        """ Return directory for openai output files for this model """
        return self.output_dir('meta', self.run_name, *args)

    def data_dir(self, *args) -> str:
        """ Directory where to store data """
        return os.path.normpath(os.path.join(self.project_dir, 'data', *args))

    def checkpoint_dir(self, *args) -> str:
        """ Return checkpoint directory for this model """
        return self.output_dir('checkpoints', self.run_name, *args)

    def openai_dir(self, *args) -> str:
        """ Return directory for openai output files for this model """
        return self.output_dir('openai', self.run_name, *args)

    @property
    def run_name(self) -> str:
        """ Return name of the run """
        return f"{self._model_name}/{self.run_number}"

    @property
    def name(self) -> str:
        """ Return name of the model """
        return self._model_name

    @property
    def meta(self) -> dict:
        """ Return name of the model """
        self.enforce_meta()
        return self._meta

    @property
    def tag(self) -> Optional[str]:
        """ Tag for this model/run number """
        return self._tag

    def render_configuration(self) -> dict:
        """ Return a nice and picklable run configuration """
        return self.provider.render_environment()

    def provide(self, name):
        """ Return a dependency-injected instance """
        return self.provider.instantiate_by_name(name)

    def provide_with_default(self, name, default=None):
        """ Return a dependency-injected instance """
        return self.provider.instantiate_by_name_with_default(name, default_value=default)

    def banner(self, command_name) -> None:
        """ Print a banner for running the system """
        if self.tag:
            print("Running model {}, run {} ({}) -- command {}".format(
                self._model_name, self.run_number, self.tag, command_name)
            )
        else:
            print("Running model {}, run {} -- command {}".format(
                self._model_name, self.run_number, command_name)
            )
        print(dtm.datetime.now().strftime("%Y/%m/%d - %H:%M:%S"))
        print("=" * 80)

    def quit_banner(self) -> None:
        """ Print a banner for running the system """
        print("=" * 80)
        print("Done.")
        print(dtm.datetime.now().strftime("%Y/%m/%d - %H:%M:%S"))
        print("=" * 80)

    def __repr__(self):
        return f"<Config at {self.filename}>"

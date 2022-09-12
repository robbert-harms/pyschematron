from __future__ import annotations

__author__ = 'Robbert Harms'
__date__ = '2022-08-23'
__maintainer__ = 'Robbert Harms'
__email__ = 'robbert@xkls.nl'


from pathlib import Path
from typing import Dict

import toml
from appdirs import user_config_dir

from pyschematron import __version__


class Config:

    def __init__(self, config: Dict):
        """Create a Config instance from the provided configuration.

        Args:
            config: the configuration (in TOML reducible format).
        """
        self._config = config

    @classmethod
    def create_empty(cls) -> Config:
        """Create an empty configuration with all options blank."""
        config = {
            'gpg_keys': {
                'dev': '',
                'qa': '',
                'prod': '',
                'staging': '',
                'sandbox': ''
            },
            'gui': {
                'auto-format-xml': True
            }
        }
        return cls(config)

    @classmethod
    def load_from_user_dir(cls) -> Config:
        """Load this config from the user config dir.

        The user config dir is automatically created based on the user environment.
        """
        config_file = cls.get_config_file()

        if not config_file.exists():
            raise FileNotFoundError('Configuration not available.')

        with open(config_file) as f:
            return Config(toml.load(f))

    @staticmethod
    def get_config_file() -> Path:
        """Get the location we write the configuration files to.

        Returns:
            The user configuration directory.
        """
        return Path(user_config_dir(appname='pyschematron',
                                    appauthor='Robbert Harms', version=__version__)) / 'config.toml'

    def save_to_user_dir(self) -> None:
        """Save the configuration to the user location."""
        self.get_config_file().parent.mkdir(parents=True, exist_ok=True)

        with open(self.get_config_file(), 'w') as f:
            toml.dump(self._config, f)

    def get_gpg_keys(self) -> Dict[str, Path]:
        """Get the location of the GPG keys from this configuration.

        Returns:
            A mapping of key names to filenames.
        """
        return {name: Path(location) for name, location in self._config['gpg_keys'].items()}

    def __str__(self):
        return toml.dumps(self._config)

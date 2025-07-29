from configparser import ConfigParser
from io import StringIO
from os import listdir
from os.path import isfile, join, isdir
from os import path, listdir

from utils import hutils

import os
import sys
import shutil
import json
import logger
import base64

logging = logger.Logger()


class Config:
    home = os.path.expanduser("~")
    dot_hst = "%s/.hst" % home
    dot_hst_config = dot_hst + "/etc"
    dot_hst_config_file = dot_hst_config + "/config"
    dot_hst_context = dot_hst + "/share"
    context = ""
    model = None
    parser = None
    instance = None

    def __new__(cls):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
            cls.instance.init()
        return cls.instance

    def init(self):
        self.parser = ConfigParser()
        self.parser.read(self.dot_hst_config_file)

        self.create_configuration()
        self.parse_configuration()

    # base32 approach (10 chars) to help avoid 1/I 0/O visual discrepancies.
    def generate_id(self):
        random_bytes = os.urandom(6)  # 6 bytes = 10 chars in base32
        id = base64.b32encode(random_bytes).decode('utf-8').rstrip('=')
        return id

    # parses the configuration of a given cli to set configured execution
    def parse_configuration(self):
        if self.parser.has_section("default"):
            for section_name in self.parser.sections():
                for name, value in self.parser.items("default"):
                    if name == "context":
                        self.context = value
        else:
            sys.exit("hst: no available configuration.")

    # creates a configuration file for a named cli
    def create_configuration(self):
        hutils.create_folder(self.dot_hst)
        hutils.create_folder(self.dot_hst_config)
        hutils.create_folder(self.dot_hst_context)

        if not os.path.exists(self.dot_hst_config_file):
            hutils.create_file(self.dot_hst_config_file)

            self.parser.read_file(StringIO(u"[default]"))
            self.parser.set("default", "context", str(self.generate_id()))
            with open(self.dot_hst_config_file, "w") as config:
                self.parser.write(config)
        else:
            logging.debug("the configuration for hst already exists. leaving the existing configuration untouched.")
            return

        logging.info("hst was successfully configured.")
        return

    def save(self):
        if os.path.exists(self.dot_hst_config_file):
            self.parser.set("default", "context", self.context)
            with open(self.dot_hst_config_file, "w") as config:
                self.parser.write(config)

    def get_context(self):
        context_file_path = self.context_file_path()
        if os.path.exists(context_file_path):
            try:
                with open(context_file_path, 'r') as f:
                    context = c.Context(json.load(f))
                    logging.debug(f"[ hst ] Loaded context from {context_file_path}")
                    return context
            except:
                logging.debug("[ hst ] Unable to open context file not found, creating new")
                return self.new()
        else:
            logging.debug("[ hst ] Context file not found, creating new")
            return self.new()

        return None

    def new(self):
        share = self.dot_hst_context
        current_context = self.dot_hst_context + "/" + self.context

        if not os.path.exists(share):
            hutils.create_folder(share)

        if not os.path.exists(current_context):
            hutils.create_folder(current_context)

        context_file_path = self.context_file_path()
        if not os.path.exists(context_file_path):
            with open(context_file_path, 'w') as f:
                context = c.Context()
                f.write(context.serialize())
                return context

        return None

    def clear(self):
        context_file_path = self.context_file_path()
        if os.path.exists(context_file_path):
            os.remove(context_file_path)
            return self.new()

        return None

    def context_file_path(self):
        return os.path.join(self.dot_hst_context, self.context, "context.json")

    def list_models(self):
        model_names = list(models.keys())
        model_names.sort()
        return model_names

# -*- coding: utf-8 -*-

#  Developed by CQ Inversiones SAS. Copyright ©. 2019 - 2025. All rights reserved.
#  Desarrollado por CQ Inversiones SAS. Copyright ©. 2019 - 2025. Todos los derechos reservados.

# ****************************************************************
# IDE:          PyCharm
# Developed by: macercha
# Date:         5/03/25
# Project:      Zibanu Django
# Module Name:  file_utils
# Description:
# ****************************************************************
import filetype
import hashlib
import logging
import os
import pathlib
from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class FileUtils:
    """ File utils class to encapsulate file operations and storage """
    HASH_METHODS = ["md5", "sha1", "sha224", "sha256", "sha384", "sha512"]
    def __init__(self, **kwargs) -> None:
        """
        Constructor of class FileUtils
        Parameters
        ----------
        kwargs:
            Set of keyword arguments passed to FileUtils, with these options.
        """
        self.__fs = FileSystemStorage()
        self.__hash_value = None
        self.__created_at = kwargs.get("created_at", None)
        if self.__created_at is None:
            self.__created_at = timezone.now()
        self.__file = kwargs.get("file", None)
        self.__file_name = kwargs.get("file_name", "")
        self.__file_dir = kwargs.get("file_dir", "")
        self.__hash_method = kwargs.get("hash_method", settings.ZB_REPOSITORY_HASH_METHOD)
        self.__use_media = kwargs.get("use_media", True)
        self.__use_datetime = kwargs.get("use_datetime", True)
        self.__overwrite = kwargs.get("overwrite", False)
        self.__suffix = None
        self.__mime_type = None
        # Set directory base for file storage.
        if self.__use_datetime:
            self.__file_dir = os.path.join(self.__file_dir, str(self.__created_at.year), str(self.__created_at.month))

        if self.__file is None and os.path.exists(self.full_file_name):
            self.__file = open(self.full_file_name, "w+b")
            self.__fs.get_valid_name(self.full_file_name)

        if self.__file is not None and isinstance(self.__file, File):
            # *****************************************************************************
            # COMMENT: Add file type and hash load in only one method.
            # Modified by: macercha
            # Modified at: 2025-04-03, 19:14
            # *****************************************************************************
            self.__load_features()


    # FileUtils class properties
    @property
    def file(self):
        """ File handler property. """
        return self.__file
    @file.setter
    def file(self, value):
        """ File handler setter. """
        self.__file = value

    @property
    def file_name(self):
        """ File name property. """
        return self.__file_name
    @file_name.setter
    def file_name(self, value):
        """ File name setter. """
        self.__file_name = value

    @property
    def hash_method(self):
        """ Hash method property. """
        return self.__hash_method
    @hash_method.setter
    def hash_method(self, value):
        """ Hash method setter. """
        self.__hash_method = value

    @property
    def full_file_name(self):
        """ Full file name property. """
        return os.path.join(self.__file_dir, self.__file_name)

    @property
    def file_dir(self):
        """ File directory property. """
        return self.__file_dir

    @property
    def file_suffix(self):
        """ File suffix property. """
        return self.__get_suffix()

    @property
    def mime_type(self):
        """ Mime type property. """
        return self.__mime_type

    @property
    def hash(self):
        """ File hash property. """
        return self.__hash_value

    @property
    def created_at(self):
        """ Created at property getter. """
        return self.__created_at

    @property
    def file_url(self):
        """ File url property getter. """
        return self.__fs.url(self.full_file_name)

    @property
    def is_valid(self):
        return self.__file is not None

    #Static Methods
    @staticmethod
    def get_hash_value(filestream: bytes, hash_method: str) -> str:
        """ Get hash value from filestream or bytes.  """
        if hash_method not in ["md5", "sha1", "sha256", "sha224"]:
            raise ValueError(_("Invalid hash method."))
        hash_value = hashlib.new(hash_method, filestream).hexdigest()
        return hash_value

    # Private methods
    def __get_suffix(self):
        """ Get file suffix property. """
        return self.__suffix


    def __load_features(self):
        """
        Load different features from file.
        Returns
        -------
        None
        """
        if self.__file is None:
            raise ValueError(_("File handler has not been set yet."))
        f_type = filetype.guess(self.__file)
        if f_type is None:
            raise ValueError(_("Cannot determine file type from file."))
        self.__suffix = pathlib.Path(self.__file.name).suffix[1:].lower()
        self.__mime_type = f_type.mime

        self.__load_hash()

    def __load_hash(self) -> str:
        """
        Load file hash.

        Returns
        -------
        str:
            File hash.
        """
        if self.__file is None:
            raise ValueError(_("File has not been set yet."))
        self.__file.seek(0)
        self.__hash_value = FileUtils.get_hash_value(self.__file.read(), self.__hash_method)
        return self.__hash_value

    # Public Methods
    def save(self) -> bool:
        """
        Save file.
        Returns
        -------
        bool:
            True if save was successful.
        """
        b_return = True
        try:
            file_save = True
            if self.__fs.exists(self.full_file_name) and not self.__overwrite:
                    file_save = False

            if file_save:
                self.__fs.save(self.full_file_name, self.__file)
        except Exception as exc:
            logging.error(str(exc))
            raise exc
        else:
            return b_return


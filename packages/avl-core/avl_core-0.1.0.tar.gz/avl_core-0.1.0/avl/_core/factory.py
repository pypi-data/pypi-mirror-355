# Copyright 2024 Apheleia
#
# Description:
# Apheleia Verification Library Factory
import fnmatch
from typing import Any


class Factory:
    _by_type = {}
    _by_instance = {}
    _variables = {}

    @staticmethod
    def set_override_by_type(original: Any, override: Any) -> None:
        """
        Set an override for a type.

        :param original: The original type to override.
        :type original: type
        :param override: The override type.
        :type override: type
        """
        if original.__name__ not in Factory._by_type:
            Factory._by_type[original.__name__] = override

    @staticmethod
    def set_override_by_instance(path: str, override: Any) -> None:
        """
        Set an override by instance path.

        :param path: The instance path to override.
        :type path: str
        :param override: The override type.
        :type override: type
        """
        if path not in Factory._by_instance:
            Factory._by_instance[path] = override

    @staticmethod
    def get_by_type(original: type) -> type:
        """
        Get the override for a type if it exists, otherwise return the original type.

        :param original: The original type.
        :type original: type
        :return: The override type or the original type.
        :rtype: type
        """
        if original.__name__ in Factory._by_type:
            return Factory._by_type[original.__name__]
        else:
            return original

    @staticmethod
    def get_by_instance(original: type, path: str) -> type:
        """
        Get the override by instance path if it exists, otherwise return the original type.

        :param original: The original type.
        :type original: type
        :param path: The instance path to look up.
        :type path: str
        :return: The override type or the original type.
        :rtype: type
        """
        matches = [value for value in Factory._by_instance if fnmatch.fnmatch(path, value)]

        if matches:
            closest_match = min(matches, key=len)
            return Factory._by_instance[closest_match]
        else:
            return original

    @staticmethod
    def get_factory_override(original: type, path: str) -> type:
        """
        Get the override for a type, name, and instance path.

        :param original: The original type.
        :type original: type
        :param name: The name to look up.
        :type name: str
        :param path: The instance path to look up.
        :type path: str
        :return: The override type or the original type.
        :rtype: type
        """
        retval = Factory.get_by_type(original)

        if path is not None:
            retval = Factory.get_by_instance(retval, path)

        return retval

    @staticmethod
    def set_variable(path: str, value: Any) -> None:
        """
        Set a variable. This is equivalent to setting a value in the UVM config_db.

        :param path: The path to the variable.
        :type path: str
        :param value: The value to set for the variable.
        :type value: Any
        """
        if path not in Factory._variables:
            Factory._variables[path] = value

    @staticmethod
    def get_variable(path: str, original: Any) -> Any:
        """
        Get the value of a variable by its path if it exists, otherwise return the original value.

        :param original: The original value to return if no match is found.
        :type original: Any
        :param path: The path to the variable.
        :type path: str
        :return: The value of the variable or the original value.
        :rtype: Any
        """
        matches = [value for value in Factory._variables if fnmatch.fnmatch(path, value)]

        if matches:
            closest_match = min(matches, key=len)
            return Factory._variables[closest_match]
        else:
            return original


__all__ = ["Factory"]

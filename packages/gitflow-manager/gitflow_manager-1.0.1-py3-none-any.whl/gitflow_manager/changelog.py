import json
import os
from copy import deepcopy
from datetime import datetime
from enum import Enum

import pystache


class Sections(Enum):
    """
    Enumerator to define possible change log sections
    """

    added = "Added"
    changed = "Changed"
    fixed = "Fixed"


class ChangeLog:
    """
    A class to create a formatted markdown change log from a mustache template and the changes as json
    """

    def __init__(
        self,
        file: str = "docs/source/change_log.rst",
        template_file: str = "docs/source/change_log.tpl",
        compare_url=None,
        version_prefix: str = "",
    ):
        """

        :param file: File name of the change log file. Has to have the rst ending
        :param template_file:  File name of the change log template. Has to be in mustache format
        :param compare_url: Git url that is used to compare commits/branches with each other. Mostly ends with /compare/
        :param version_prefix: Optional prefix that will be added to the version string before creating the log data
        """
        assert file.endswith(".rst"), 'Change log file name has to end with ".rst"'
        self.file_name = file
        self.data = {}
        if not os.path.isfile(self.file_name.replace(".rst", ".json")):
            self.create_empty_json()
        if not os.path.isfile(template_file):
            self.create_default_tpl(template_file)
        self.read_json()
        self.compare_url = compare_url
        self.version_prefix = version_prefix
        with open(template_file) as fh:
            self.template = fh.read()
        self.renderer = pystache.Renderer()

    @staticmethod
    def create_default_tpl(template_file):
        with open(template_file, "w") as fh:
            fh.write(
                "{{#general}}\n"
                "{{{title}}}\n"
                "------------------\n"
                "{{{description}}}\n"
                "{{/general}}\n\n"
                "{{#versions}}\n"
                "{{{version}}}\n"
                "-------------\n"
                "**Release Date:** {{{date}}}\n\n"
                "{{#sections}}\n"
                "{{{label}}}\n"
                "~~~~~~~~~~~~~\n"
                "{{#entries}}\n"
                "- {{{message}}} [{{{author}}}]\n"
                "{{/entries}}\n\n"
                "{{/sections}}\n"
                "{{/versions}}\n\n"
                "Changes comparison\n"
                "------------------\n"
                "{{#version_comparison}}\n"
                "- **[{{version}}]**: `<{{{url}}}>`_\n"
                "{{/version_comparison}}\n"
            )

    def create_empty_json(self):
        json_path = self.file_name.replace(".rst", ".json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w") as fh:
            json.dump({"versions": []}, fh, indent=4)

    def read_json(self):
        """
        Read JSON data from a file and ensure version info is sorted in descending date order.

        """
        with open(self.file_name.replace(".rst", ".json")) as fh:
            data = json.load(fh)
        # assert version info sorted in descending date order
        data["versions"] = sorted(
            data["versions"],
            key=lambda x: x["date"] if x["date"] != "" else "Z",
            reverse=True,
        )
        self.data = data

    def write_json(self):
        with open(self.file_name.replace(".rst", ".json"), "w") as fh:
            json.dump(self.data, fh, indent=4)

    def get_version(self, version: str) -> None | dict:
        """
        Returns a copy of the change log for the requested version

        :param version: The requested version as string
        :return: The version's change log as dict
        """
        for version_dict in self.data["versions"]:
            if version_dict["version"] == self.version_prefix + version:
                return deepcopy(version_dict)
        return None

    @staticmethod
    def ask_for_changes(user: str, sections: list[Sections], app_specific_changes, app_specific_text) -> list:
        """
        This method asks interactively for changes and returns a section list ready to be handed over to ChangeLog

        :param user: Name of the user, who did the changes. Should be the git user name if possible
        :param sections: A list of sections that should be added
        :param app_specific_changes:
        :param app_specific_text:
        :return: A list of sections and changes to add into ChangeLog.
        """
        section_list = []
        for section in sections:
            assert isinstance(section, Sections), 'List entries have to be values from the Enum "Sections"!'
            sec_string = section.value
            entries = []
            while True:
                if not app_specific_changes:
                    answer = input(
                        f"Any (more) changes to document for section \n'{sec_string}'\n? "
                        f"(Type the change or enter nothing for continuing)\n"
                    )
                else:
                    app_specific_text = app_specific_text.format(sec_string)
                    answer = input(app_specific_text)
                if answer == "":
                    break
                else:
                    entries.append({"author": user, "message": answer})
            if entries:
                section_list.append({"label": sec_string, "entries": entries})
        return section_list

    @staticmethod
    def _add_sections(version_dict: dict, sections: dict) -> dict:
        """
        Add sections and their entries to an existing version dictionary.

        :param version_dict: The versions as a dictionary to which sections and entries will be added.
        :param sections: A dictionary containing sections and their entries to be added to the versions.
        :return: The updated version dictionary with sections and entries.
        """
        label_dict = {}
        for n, section in enumerate(version_dict["sections"]):
            label_dict[section["label"]] = n
        for section in sections:
            label = section["label"]
            if label not in label_dict:
                # create section
                version_dict["sections"].append({"label": label, "entries": []})
                label_dict[label] = len(version_dict["sections"]) - 1
            # add all messages of unrel_dicts section to this section
            version_dict["sections"][label_dict[label]]["entries"].extend(section["entries"])
        return version_dict

    def create_new_version(self, new_version: str, new_sections=None):
        """
        Adds a new version to the change log

        :param new_version: String of the new version, such as v0.5.2 . If the changes are still for an unreleased \
        state, use None!
        :param new_sections: A formatted list of new_sections, obtained from method ask_for_changes
        """
        if new_version is None or new_version=="Unreleased":
            new_version = "Unreleased"
        else:
            new_version = self.version_prefix + new_version
        date_ = datetime.now().strftime("%Y-%m-%d %H:%M") if new_version != "Unreleased" else ""

        found = False
        # search for existing version with same string (forbidden) or Unreleased tag (will be moved into new version)
        for version_dict in self.data["versions"]:
            # remember, self.data is a dict (i.e. mutable) so all changes directly apply to it
            if version_dict["version"] == new_version and new_version != "Unreleased":
                raise Exception(
                    f"Version {new_version} already exists! Use method add_to_version if you want to add "
                    f"sections to an existing version!"
                )
            elif version_dict["version"] == "Unreleased":
                found = True
                version_dict["version"] = new_version
                version_dict["date"] = date_
                if new_sections is not None:
                    # add new sections. No need to get result as dicts are mutable
                    self._add_sections(version_dict, new_sections)

        if not found:
            if new_sections is None:
                raise Exception(
                    "No entry found for Unreleased version and no new version information added. "
                    "Adding empty new version is not allowed!"
                )
            else:
                self.data["versions"].insert(0, {"version": new_version, "date": date_, "sections": new_sections})

        # update the json file
        self.write_json()

    def add_to_version(self, version: str | None, new_sections):
        """
        Adds change logs to an existing version

        :param version: String of the version to add changes to, such as v0.5.2 . If the changes are still for an \
        unreleased state, use None!
        :param new_sections: A formatted list of new_sections, obtained from method ask_for_changes
        """
        if version is None or version=="Unreleased":
            version = "Unreleased"
        else:
            version = self.version_prefix + version
        found = False
        for version_dict in self.data["versions"]:
            # remember, self.data is a dict (i.e. mutable) so all changes directly apply to it
            if version_dict["version"] == version:
                found = True
                # add new sections. No need to get result as dicts are mutable
                self._add_sections(version_dict, new_sections)

        if not found:
            if version == "Unreleased":
                self.create_new_version(new_version=version, new_sections=new_sections)
            else:
                raise Exception(
                    f"No entry found for version {version}! If you want to create a new version, use method "
                    "create_new_version!"
                )

        # update the json file
        self.write_json()

    def _add_branch_comparison(self, data: dict):
        """
        Add a list of comparisons between commits/branches in data dictionary.
        :param data: The dictionary to which the comparison info will be added, also contains the version info
        :return: The updated data dictionary with branch comparison information.
        """
        if self.compare_url is not None:
            if "version_comparison" in data:
                data.pop("version_comparison")
            # assumes the dict is ordered by date!!
            newer_version = None
            comparison_list = []
            for version_dict in data["versions"]:
                if newer_version is None:
                    newer_version = version_dict["version"]
                else:
                    comparison_list.append(
                        {
                            "version": newer_version,
                            "url": f"{self.compare_url}/diff?targetBranch=tags/{version_dict['version']}&sourceBranch="
                            f"{'tags/'+newer_version if newer_version != 'Unreleased' else 'heads/dev'}",
                        }
                    )
            data["version_comparison"] = comparison_list
        return data

    def write_log(self):
        """
        Write changes to the ChangeLog file.
        """
        extended_data = self._add_branch_comparison(self.data)
        with open(self.file_name, "w") as fh:
            fh.write(self.renderer.render(self.template, extended_data))

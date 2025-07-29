import os
from functools import lru_cache
from ara_cli.classifier import Classifier
from ara_cli.artefact_link_updater import ArtefactLinkUpdater
from ara_cli.artefact_reader import ArtefactReader
from ara_cli.artefact_models.artefact_model import Contribution
from ara_cli.template_manager import DirectoryNavigator
from ara_cli.artefact_fuzzy_search import suggest_close_name_matches
import re


class ArtefactRenamer:
    def __init__(self, file_system=None):
        self.file_system = file_system or os
        self.link_updater = ArtefactLinkUpdater()

    @lru_cache(maxsize=None)
    def navigate_to_target(self) -> str:
        navigator = DirectoryNavigator()
        original_directory = navigator.navigate_to_target()
        return original_directory

    @lru_cache(maxsize=None)
    def compile_pattern(self, pattern):
        return re.compile(pattern)

    def rename(self, old_name, new_name, classifier):
        if not new_name:
            raise ValueError("New name must be provided for renaming.")
        if not Classifier.is_valid_classifier(classifier):
            raise ValueError("Invalid classifier provided. Please provide a valid classifier.")

        fs = self.file_system
        original_directory = self.navigate_to_target()
        original_directory = fs.path.abspath(original_directory)

        classified_artefacts = ArtefactReader.read_artefacts()

        artefacts_by_current_classifier = classified_artefacts.get(classifier, [])
        matching_artefacts = list(filter(lambda a: a.title == old_name, artefacts_by_current_classifier))

        if not matching_artefacts:
            all_artefact_names = [artefact.title for artefact in artefacts_by_current_classifier]
            suggest_close_name_matches(old_name, all_artefact_names)
            return

        matching_artefact = matching_artefacts[0]

        old_file_path = matching_artefact.file_path
        old_base_path = fs.path.dirname(old_file_path)
        old_dir_path = f"{old_base_path}/{old_name}.data"

        old_dir_exists = fs.path.exists(old_dir_path)

        if not fs.path.exists(old_file_path):
            raise FileNotFoundError(f"The file {old_file_path} does not exist.")

        children_by_classifier = ArtefactReader.find_children(
            artefact_name=old_name,
            classifier=classifier,
            classified_artefacts=classified_artefacts
        )

        matching_artefact.title = new_name
        new_file_path = matching_artefact.file_path
        new_base_path = fs.path.dirname(new_file_path)
        new_dir_path = f"{new_base_path}/{new_name}.data"
        if fs.path.exists(new_file_path):
            raise FileExistsError(f"The new file name {new_file_path} already exists.")
        if fs.path.exists(new_dir_path):
            raise FileExistsError(f"The new directory name {new_dir_path} already exists.")

        serialized_artefact = matching_artefact.serialize()
        with open(matching_artefact.file_path, 'w') as file:
            file.write(serialized_artefact)
        fs.remove(old_file_path)

        absolute_old_file_path = fs.path.abspath(old_file_path)
        absolute_new_file_path = fs.path.abspath(new_file_path)
        print(f"Renamed file: {absolute_old_file_path} to {absolute_new_file_path}")

        if old_dir_exists:
            absolute_old_dir_path = fs.path.abspath(old_dir_path)
            absolute_new_dir_path = fs.path.abspath(new_dir_path)
            fs.rename(old_dir_path, new_dir_path)
            print(f"Renamed directory: {absolute_old_dir_path} to {absolute_new_dir_path}")

        for children in children_by_classifier.values():
            for child in children:
                contribution = child.contribution
                contribution.artefact_name = new_name
                child.contribution = contribution
                serialized_artefact = child.serialize()
                with open(child.file_path, 'w') as file:
                    file.write(serialized_artefact)

        fs.chdir(original_directory)

    def _update_title_in_artefact(self, artefact_path, new_title, classifier):
        # Format the new title: replace underscores with spaces
        formatted_new_title = new_title.replace('_', ' ')

        # Get the artefact title prefix using the classifier
        title_prefix = Classifier.get_artefact_title(classifier.lower())

        if not title_prefix:
            raise ValueError(f"Invalid classifier: {classifier}")

        # Read the file content
        with open(artefact_path, 'r') as file:
            content = file.read()

        # Find the old title line
        old_title_line = next((line for line in content.split('\n') if self.compile_pattern(f"^{title_prefix}").match(line)), None)
        if old_title_line is None:
            raise ValueError(f"The artefact file does not contain the title prefix '{title_prefix}'.")

        # Construct the new title line without adding an extra colon
        new_title_line = f"{title_prefix}: {formatted_new_title}"
        # Replace the old title line with the new title line in the content
        new_content = content.replace(old_title_line, new_title_line, 1)

        # Write the updated content back to the file
        with open(artefact_path, 'w') as file:
            file.write(new_content)

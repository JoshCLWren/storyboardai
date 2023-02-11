"""
Sketch of the models for the Storyboard app.
Also contains script to marshall the files into the proper directory/file structure.

"""

import json
import os
import shutil
import uuid
from dataclasses import dataclass
from typing import List


@dataclass
class StoryStructure:
    """
    A Story Structure object represents the folder and file structure of a Story.
    """

    path: str = None
    cache_path: str = None
    title: str = None
    text: str = None
    length: int = 0
    id: str = str(uuid.uuid4())
    output_folder: str = (
        f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/output/{title}"
    )
    progress: int = 0
    config: dict = None
    global_prompt_prefix: str = "Prompt: "
    global_prompt_suffix: str = " "

    def __post_init__(self):
        """
        Create the output folders for the story.
        And the yaml file for the story.
        """
        if not os.path.exists(self.output_folder):
            os.mkdir(self.output_folder)
        for folder in ["audio", "video", "images", "final_video", "cache", "text"]:
            if not os.path.exists(f"{self.output_folder}/{folder}"):
                os.mkdir(f"{self.output_folder}/{folder}")

        # create the yaml config file for the story
        with open(f"{self.output_folder}/config.yaml", "w") as f:
            f.write(
                {
                    "id": self.id,
                    "title": self.title,
                    "path": self.path,
                    "progress": self.progress,
                    "length": self.length,
                    "text": self.text,
                    "config": self.config,
                    "global_prompt_prefix": self.global_prompt_prefix,
                    "global_prompt_suffix": self.global_prompt_suffix,
                }.__str__()
            )

        # create the cache file for the story
        with open(f"{self.output_folder}/cache/{self.id}_{self.id}.json", "w") as f:
            cache_dict = {
                "id": str(self.id),
                "title": self.title,
                "path": self.path,
                "progress": self.progress,
                "length": self.length,
                "text": self.text,
                "config": self.config,
            }
            json.dump(cache_dict, f)
        if not self.title:
            print("No title provided, enter a title for the story.")
            self.title = input()

    def save_cache(self):
        """
        Save the cache file for a story.
        Returns:

        """
        with open(f"{self.output_folder}/cache/{self.id}.json", "w") as f:
            self.id = str(self.id)
            json.dump(self.__dict__, f)

    def load_cache(self):
        """
        Load the cache file for a story.
        Returns:

        """
        with open(f"{self.output_folder}/cache/{self.id}.json", "r") as f:
            cache = json.load(f)
        self.__dict__ = cache

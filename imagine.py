"""
This is a script that attempts to parse a txt file and create images for each line,
audio for each line, and a video of the images and audio.
"""

import contextlib
import json
import os
import random
import shutil
import subprocess
import time
from dataclasses import dataclass
from uuid import uuid4

import arrow
import av
import scripts
import torch
import yaml
from gtts import gTTS
from moviepy.editor import *
from PIL import Image, ImageDraw, ImageFont
from transformers import BartForConditionalGeneration, BartTokenizer


@dataclass
class ImageOptions:
    """
    This class stores different options and styles that are available to add to an image prompt.
    """

    genres = random.choice(["stuff"])
    artists = random.choice(["stuff"])
    adjectives = random.choice(["stuff"])
    trends: str = "trending on artstation and unreal engine"
    seed: int = random.randint(1, 1000000)

    def set_options(self):
        """

        Returns:

        """
        return f"{self.genres}, {self.artists}, {self.adjectives}, {self.trends}"


@dataclass
class Photography:
    """
    This class stores different Photography Enums to add to an image prompt.
    """

    shot_type = random.choice(
        (
            "close-up",
            "extreme close-up",
            "POV",
            "medium close-up",
            "medium shot",
            "long shot",
        )
    )
    style = random.choice(
        ("polaroid", "Monochrome", "Long Exposure", "Color Splash", "Long Shot")
    )
    lighting = random.choice(("soft", "ambient", "Ring", "Sun", "Cinematic"))
    lens = random.choice(
        ("Wide-Angle", "Telephotot", "24mm", "EF 70mm", "Bokeh", "Macro")
    )
    device = random.choice(("iPhone X", "CCTV", "Nikon Z FX", "Canon", "Gopro"))

    def set_photography(self):
        """
        A method that returns the randomly  generated string from the class's attributes.
        Args:
            self
        Returns:
            photography_string
        """
        return (
            f"{self.shot_type} {self.style} {self.lighting} {self.lens} {self.device}"
        )


@dataclass
class GlobalPrompt:
    """
    The Global image Prompt class
    """

    photography_string: str = Photography().set_photography()
    art_medium = random.choice(
        [
            "chalk",
            "graffiti",
            "water colors",
            "oil paints",
            "cinematic",
            "4k",
            "hyper realistic",
            "12k",
            "fabric",
            "pencil drawing",
            "wood",
            "clay",
        ]
    )
    artist = None

    def global_prompt_prefix(self, artist=None):
        if artist:
            return f"A {self.art_medium} in the style of {artist}"
        else:
            return f"A {self.art_medium}"

    def global_prompt_suffix(self):
        return f"with a {self.photography_string} photography style"


@dataclass
class Story:
    """
    A class that represents a story. It contains the text of the story, the
    images of the story, the audio of the story, and the video of the story.
    and all the other stuff
    """

    file_path = None
    global_prompt = GlobalPrompt()

    file_prefix = None
    end_time: str = None
    start_time: str = arrow.now()
    text: str = None
    story_dict: list = None

    cached: bool = False
    cache_path: str = None
    last_updated = arrow.now().isoformat()
    ignore_cache = False
    global_prompt_prefix = global_prompt.global_prompt_prefix()
    global_prompt_suffix = global_prompt.global_prompt_suffix()
    id = None
    config = None
    load: bool = False

    def __post_init__(self):
        # check if a folder exists for the story to determine if we're loading or not
        if not self.load:
            self.id = uuid4()
            self.cache_path = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/output/{self.id}/cache"
            # make the folders for the story
            os.mkdir(
                f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/output/{self.id}"
            )
            os.mkdir(self.cache_path)
            self.file_prefix = f"{self.id}_"
            print(f"story id for debugging purposes: {self.id}")
            prefix_approval = input(
                f"Are you ok with this prompt prefix: {self.global_prompt_prefix}?"
            )
            if prefix_approval.lower().startswith("n"):
                self.global_prompt_prefix = input("Enter your own prefix: ")
            suffix_approval = input(
                f"Ok, but what about this suffix: {self.global_prompt_suffix}?"
            )
            if suffix_approval.lower().startswith("n"):
                self.global_prompt_suffix = input("Enter your own suffix: ")
        else:
            # load the config yaml for the story
            print("enter the id of the story you want to load:")
            self.id = input()
            self.file_prefix = f"{self.id}_"
            self.file_path = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/output/{self.id}"
            try:
                breakpoint()
                with open(
                    f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/output/{self.id}/config.yaml",
                    "r",
                ) as config:
                    self.config = yaml.load(config, Loader=yaml.FullLoader)
                    self.global_prompt_prefix = self.config["global_prompt_prefix"]
                    self.global_prompt_suffix = self.config["global_prompt_suffix"]
                    self.text = self.config["text_path"]
            except FileNotFoundError:
                print("No config file found. Exiting.")
                exit()

    def get_text(self):
        """
        This function gets the text file and prepares it for parsing.
        Returns:
            list: a list of dictionaries with a text key and the value of each line.
        Example:
            [{'text': 'This is the first line.'}, {'text': 'This is the second line.'}]
        """

        paraphrase_model = Paraphraser()

        if self.file_path and os.path.exists(self.file_path) and not self.ignore_cache:
            print(f"Getting text from {self.file_path}")
            try:
                with open(self.file_path, "r") as text:
                    story = [
                        line[:-1]
                        for line in text
                        if not line.startswith("The AI response returned in")
                        and line not in ["", " "]
                    ]

                story_dict = [
                    paraphrase({"text": line}, paraphrase_model)
                    for line in story
                    if len(line) > 0 or line != b""
                ]
                # remove any dictionaries that look like {"text": ""} or
                story_dict = [line for line in story_dict if line["text"] != ""]
                story_dict.append(
                    {"file_prefix": self.file_prefix, "file_path": self.file_path}
                )
                print("Caching story")
                self.cache_story()
                print("Text parsed")
                self.text = story
                self.story_dict = story_dict
                return story_dict
            except FileNotFoundError:
                print("No text file found. Making a new one.")
        else:
            print("No file path provided")
            print("Paste the text of your story here:")
            story_in = input()
            story = [
                line
                for line in story_in.split("\n")
                if not line.startswith("The AI response returned in")
                and line not in ["", " "]
            ]
            story_dict = [
                paraphrase({"text": line}, paraphrase_model)
                for line in story
                if len(line) > 0 or line != b""
            ]
            # remove any dictionaries that look like {"text": ""} or
            story_dict = [line for line in story_dict if line["text"] != ""]
            story_dict.append(
                {"file_prefix": self.file_prefix, "file_path": self.file_path}
            )
            print("Caching story")
            self.cache_story()
            print("Text parsed")
            self.text = story
            self.story_dict = story_dict
            return story_dict

    def generate_audio(self):
        """
        This function takes the story dictionary and generates audio for each line using gTTS.
        Args:
            story_dict:

        Returns:
            list: a list of dictionaries with a text key and the value of each line with an audio key
            and the value of the audio file name.
        Example:
            [{'text': 'This is the first line.', 'audio': 'audio_0.mp3'}, {'text': 'This is the second line.', 'audio': 'audio_1.mp3'}]

        """
        # check if the audio folder exists
        # if not, create it
        print("Checking for audio folder")
        if not os.path.exists(
            f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/audio/{self.file_prefix}"
        ):
            print("Audio folder not found, creating it")
            os.makedirs(
                f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/audio/{self.file_prefix}"
            )
        print("Audio folder found")
        for index, line in enumerate(self.story_dict):
            # check if the audio file already exists
            # if it does, skip it
            # if not, generate the audio file
            # skip the last modified key
            if not line.get("text"):
                print(f"Skipping {line} as there is no text for this index")
            if not self.ignore_cache:
                print(f"Checking for audio file for line {index}")
                if os.path.exists(
                    f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/audio/{self.file_prefix}/audio_{index}.mp3"
                ):
                    print(f"Audio file for line {index} found")
                    line["audio"] = f"audio_{index}.mp3"
                    continue

            try:
                print(f"Audio file for line {index} not found, generating it")
                tts = gTTS(text=line["text"], lang="en")
                tts.save(
                    f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/audio/{self.file_prefix}/audio_{index}.mp3"
                )
                line[
                    "audio"
                ] = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/audio/{self.file_prefix}/audio_{index}.mp3"
            except Exception as e:
                print(e)
                print(f"Audio file for line {index} could not be generated, {line}")
        print("Audio generated")
        self.cache_story()

    def cache_story(self):
        """
        This function takes the story dictionary and caches the story as a json file.

        Returns:
            None
        """

        print("let's cache this story")
        # self.cache_path = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/output/{self.id}/cache/{self.file_prefix}.json"
        if not os.path.exists(self.cache_path):
            print("Cache file not found, creating it")
            breakpoint()
            os.mkdir(
                f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/output/{self.id}/cache"
            )
            with open(self.cache_path, "w") as cache:
                json.dump(self.story_dict, cache)
        try:
            with open(self.cache_path, "w") as story:
                # find the last_updated key
                # if it exists, update it
                # if not, add it
                json.dump(self.story_dict, story)
            print("Story cached")
            self.last_updated = arrow.now().isoformat()
            self.cached = True
        except Exception as e:
            print(e)
            print("Story could not be cached")
            self.cached = False

    def generate_images(self):
        """
        This function uses scripts/txt2img.py to generate images for each line.

        Args:
            story_dict:
        example:
            [{'text': 'This is the first line.', 'audio': 'audio_0.mp3'},
            {'text': 'This is the second line.', 'audio': 'audio_1.mp3'}]

        Returns:
            [{'text': 'This is the first line.', 'audio': 'audio_0.mp3', 'image': 'image_0.png'},
            {'text': 'This is the second line.', 'audio': 'audio_1.mp3', 'image': 'image_1.png'}]
        """
        # check if the images folder exists
        # if not, create it

        for index, line in enumerate(self.story_dict):
            # check if the image file already exists
            # if it does, skip it
            # if not, generate the image file
            # skip the last modified key
            if not self.ignore_cache:
                print(f"Checking for image file for line {index}")
                if os.path.exists(
                    f"outputs/txt2img-samples/image_{self.file_prefix}_image_{index}.png"
                ):
                    print(f"Image file for line {index} found")
                    line[
                        "image"
                    ] = f"outputs/txt2img-samples/image_{self.file_prefix}_image_{index}.png"
                    continue
            try:
                print(f"Image file for line {index} not found, generating it")
                # run the txt2img.py script with the line text as the prompt
                filename = self.generate_txt2img(
                    f'{line["text"]}'.replace(":", " "),
                    index,
                )
                line[
                    "image"
                ] = f"outputs/txt2img-samples/image_{self.file_prefix}_image_{index}.png"
                print(f"Image file for line {index} generated")
            except Exception as e:
                print(e)
                print(f"Image file for line {index} could not be generated, {line}")

        self.cache_story()

    def generate_txt2img(self, text, line_index):
        """
        This function runs the txt2img.py script with the line text as the prompt.
        Args:
            text: str the prompt to overlay
            line_index: int the index of the line in the story
        Returns:
            the path to the image file generated by the script
        """
        script_file = "scripts/txt2img.py"
        prompt = f"{self.global_prompt_prefix}, {{{text}}} {self.global_prompt_suffix}"
        print(f"Running {script_file} with {prompt}")
        try:
            subprocess.run(
                [
                    "python",
                    script_file,
                    "--prompt",
                    prompt,
                    "--n_samples",
                    "1",
                    "--n_iter",
                    "1",
                    "--plms",
                    "--name",
                    f"{self.file_prefix}_image_{line_index}",
                ]
            )
        except Exception as e:
            print(e)
            print(f"Image file for {line_index} could not be generated")
            return None
        return (
            f"outputs/txt2img-samples/image_{self.file_prefix}_image_{line_index}.png"
        )

    def generate_video(self):
        """
        This function uses the story dictionary to generate a video using moviepy.
        Args:
            story_dict:
            [{'text': 'This is the first line.', 'audio': 'audio_0.mp3', 'image': 'image_0.png'},
            {'text': 'This is the second line.', 'audio': 'audio_1.mp3', 'image': 'image_1.png'}]

        Returns:
            video.mp4

        """
        # check if the video folder exists
        # if not, create it
        print("Checking for video folder")
        if not os.path.exists(
            f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/video/{self.file_prefix}"
        ):
            print("Video folder not found, creating it")
            os.makedirs(
                f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/video/{self.file_prefix}"
            )
        else:
            print("Video folder found")
        for index, line in enumerate(self.story_dict):
            line[
                "video"
            ] = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/video/{index}.mp4"
            if line.get("last_updated"):
                continue
            if not self.ignore_cache:
                print(f"Checking for video file for line {index}")
                if os.path.exists(
                    f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/video/{self.file_prefix}/{index}.mp4"
                ):
                    print(f"Video file for line {index} found")
                    continue
            try:
                try:
                    audio_clip = AudioFileClip(
                        f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/audio/{self.file_prefix}/{line['audio']}"
                    )
                except Exception as e:
                    audio_clip = AudioFileClip(line["audio"])
                image_clip = ImageClip(
                    line["image"], duration=audio_clip.duration
                ).set_audio(audio_clip)
                image_clip.write_videofile(
                    f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/video/{self.file_prefix}/{index}.mp4",
                    fps=24,
                )
            except Exception as e:
                print(e)
                continue
        self.cache_story()

    def concatenate_videos(self):
        """
        This function concatenates all the videos into one final video.
        Args:
            video_directory: str the directory containing the videos to concatenate
            output_file: str the path to the output file
        Returns:
            None
        """
        # Get a list of all the video files in the directory
        import re

        video_directory = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/video/{self.file_prefix}/"
        output_path = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/final_video/{self.file_prefix}"
        output_file = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/final_video/{self.file_prefix}/final_video.mp4"
        video_files = [f for f in os.listdir(video_directory) if f.endswith(".mp4")]
        # ensure that the files are in order from storyboard/video/0.mp4 to n and retain the order and path
        # create the final video directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        video_files = sorted(
            video_files, key=lambda x: int(re.search(r"\d+", x).group())
        )
        # Create the concat demuxer file
        with open("concat_list.txt", "w") as f:
            for video_file in video_files:
                f.write(f"file {video_directory}/{video_file}'\n")
        concat_file = "concat_list.txt"

        # Use FFmpeg to combine the videos using the concat demuxer
        command = f"ffmpeg -f concat -safe 0 -i {concat_file} -c copy {output_file}"
        os.system(command)
        # delete the concat demuxer file
        os.remove(concat_file)

    def check_if_final_video_exists(self):
        """
        This function checks if the final video exists.
        Args:
            None
        Returns:
            bool
        """
        return bool(
            os.path.exists(
                f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/final_video/{self.file_prefix}/final_video.mp4"
            )
        )

    def regenerate_images(self):
        """
        This function iterates through each line of the story text and displays the current image.
        The user can then choose to regenerate the image or not with the same prompt or a different one.
        After the image is processed it is displayed to the user and they can choose to keep it or
        make a new one with the same prompt or not. Once the image is approed it is renamed to <index>.png and
        moved to the output/id/image folder.
        Args:
            None
        """
        document = open(self.text, "r")
        lines = document.readlines()
        for line_index, line in enumerate(lines):
            print(f"Line {line_index}: {line}")
            approved = False
            image_path = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/output/{self.id}/images/{line_index}.png"
            if os.path.exists(image_path):
                self.load_image(image_path)
            print("Image already exists, do you want to regenerate it?")
            while not approved:
                if input("y/n: ").lower() == "y":
                    print("Do you want to use the same prompt?")
                    prompt = f"{self.global_prompt_prefix} {line} {self.global_prompt_suffix}"
                    print(f"Prompt: {prompt}")
                    same_prompt = input("y/n: ")
                    if same_prompt.lower() != "y":
                        print("What is the new prompt prefix?")
                        prefix_prompt = input()
                        print("What is the new prompt suffix?")
                        suffix_prompt = input()
                        prompt = f"{prefix_prompt} {line} {suffix_prompt}"
                    print("Generating image")
                    image_path = self.generate_txt2img(prompt, line_index)
                    self.load_image(image_path)
                    print("Image generated")
                    print("Do you want to keep this image?")
                    if input("y/n: ").lower() == "y":
                        approved = True

    def load_image(self, image_path):
        image = Image.open(image_path)
        image.show()


@dataclass
class Paraphraser:
    model = BartForConditionalGeneration.from_pretrained("eugenesiow/bart-paraphrase")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    tokenizer = BartTokenizer.from_pretrained("eugenesiow/bart-paraphrase")


def paraphrase(text_input: dict, paraphraser_model):
    """
    Takes a sentence and sums it up into a more cohesive idea using the BartForConditionalGeneration model.
    Args:
        text_input:a dict with a "text" key
        paraphraser_model: an instance of a Paraphraser

    Returns:
        the first index of the generated string
    """
    # split the text_input into seperate sentences and paraprhase each
    parapraph_split = text_input["text"].split(".")

    output = []
    for sentence in parapraph_split:
        print(f"Attempting to paraphrase: {sentence}")
        batch = paraphraser_model.tokenizer(sentence, return_tensors="pt")
        generated_ids = paraphraser_model.model.generate(batch["input_ids"])
        generated_sentence = paraphraser_model.tokenizer.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]
        if sentence != generated_sentence:
            print(f"Paraphrased sentence: {generated_sentence}")
        output.append(generated_sentence)
    return {"text": "".join(output)}


def initiate_story(story):
    print("Getting text...")
    story.get_text()
    print("Generating audio...")
    story.generate_audio()
    print("Generating images...")
    story.generate_images()
    print("Generating Video...")
    story.generate_video()
    print("Generating final video...")
    story.concatenate_videos()
    story.end_time = arrow.now()
    elapsed_time = story.end_time - story.start_time
    print(
        f"Job took: {elapsed_time.total_seconds()} seconds or {elapsed_time.total_seconds() / 60} minutes"
    )
    print(story.id)


def user_input():
    """
    Wherein the user inputs their options.
    Returns:
        Void
    """
    print("Enter txt file path or press enter to use default file")
    file_path = input()
    if not file_path:
        default_file = "input/sample.txt"
        file_path = default_file
    if not os.path.exists(file_path):
        print("File not found")
        exit()
    users_story = Story()
    users_story.file_path = file_path
    if not users_story.id:
        users_story.id = uuid.uuid4()
    if not users_story.file_path:
        users_story.file_path = file_path
    if not users_story.text:
        users_story.text = file_path
    if users_story.check_if_final_video_exists():
        print("Final video found, do you want to regenerate it?")
        regenerate = input("Enter y or n")
        if regenerate.lower().startswith("n"):
            print("Exiting")
            exit()
        else:
            users_story.ignore_cache = True
    return users_story


if __name__ == "__main__":
    print("Are you making a new story or regenerating images from a story?")
    print("Enter 1 for new story or 2 for regenerating images")
    user_choice = input()
    if user_choice == "1":
        story = user_input()
        initiate_story(story)
    elif user_choice == "2":
        print("Which story do you want to regenerate images for?")
        story = Story(load=True)
        story.regenerate_images()
        story.generate_audio()
        story.generate_video()
        story.concatenate_videos()
        story.end_time = arrow.now()
        elapsed_time = story.end_time - story.start_time
        print(
            f"Job took: {elapsed_time.total_seconds()} seconds or {elapsed_time.total_seconds() / 60} minutes"
        )
        print(story.id)
    else:
        print("Invalid input")
        exit()

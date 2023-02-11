"""
GUI for Storyboard.
Goals:
- Load a storyboard object by uuid
- display the matching text, prompt, auido files, video files, and images along with the final video
- allow the user to edit the text and prompt
- allow the user to generate all or some of the audio, video, and images
- Main feature will be to allow the user to rerender any image with a new prompt, text or the same prompt, text
- allow the user to save the storyboard object
- allow the user to create a new storyboard object
- allow the user to delete a storyboard object
- allow the user to export the final video
A 'Storyboard' is:
- an id (uuid4)
- a text file path
- a prompt which is the prefix and suffix for each line of text
- a list of audio files
- a list of video files
- a list of images
- a final video
- a cache directory
The directory for each storyboard's audio files is located at:
    storyboard/audio/<uuid>/audio_<index>.mp3
The directory for each storyboard's video files is located at:
    storyboard/video/<uuid>/<index>.mp4 # TODO: change this to match the same file name format as audio
The directory for each storyboard's image files is located at:
    output/txt2img-samples/image_<id>_<id>_image_<index>.png # TODO: change this to match the same file name format as audio
The directory for each storyboard's final video is located at:
    storyboard/final_video/<id>_<id>/final_video.mp4 #TODO: change this to match the same file name format as audio
The directory for each storyboard's cache is located at:
    storyboard/cache/<id>_<id>.json
The Storyboard script in imagine.py can be ran to generate the audio, video, images, and final video for a given storyboard
"""

import json
import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import PIL.Image
import PIL.ImageTk
from PIL import Image, ImageTk

# create the generate_all_models window
root = tk.Tk()
root.title("Storyboard")
root.geometry("1024x768")

# create the generate_all_models frame
mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(tk.N, tk.W, tk.E, tk.S))
mainframe.columnconfigure(0, weight=1)


# method to find all cached storyboards
def find_cached_storyboards():
    """
    Find all cached storyboards in the storyboard/cache directory.
    Returns:
        A list of cached storyboards.
    """

    # get the path to the cache directory
    cache_dir = "storyboard/cache"

    # get all the cached storyboards
    cached_storyboards = [file for file in os.listdir(cache_dir)]

    # return the cached storyboards
    print(cached_storyboards)
    return cached_storyboards


# widget to manually enter a uuid to load a storyboard
uuid = tk.StringVar()
uuid_entry = ttk.Entry(mainframe, width=7, textvariable=uuid)
uuid_entry.grid(column=1, row=1, sticky=(tk.W, tk.E))


# once the storyboard is loaded display the video files for each line of text with a play button
# once the user clicks the play button, play the video file
from dataclasses import dataclass


@dataclass
class StoryBoard:
    """
    A Storyboard object.
    """

    id: str
    audio_files: list
    video_files: list
    images: list
    final_video: str
    cache: list


# method to display the storyboard object from the uuid in the cached_storyboards widget
def load_storyboard():
    """
    Load storyboard object.
    Args:

    Returns:
        A Storyboard object.
    """

    # find the uuid from the cache path example: "/Users/joshwren/Code/playground/stable-diffusion/storyboard/cache/08e3d70c-fa2d-4e2b-9d9c-1b1c55712e9e_08e3d70c-fa2d-4e2b-9d9c-1b1c55712e9e.json"
    story_id = None
    try:
        cache_path = cached_storyboards.get()
        story_id = cache_path.split("/")[-1].split("_")[0]
    except Exception:
        # user may have manually entered a uuid
        story_id = cached_storyboards.get()
        cache_path = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/cache/{story_id}_{story_id}.json"

    images = [
        image
        for image in os.listdir("./outputs/txt2img-samples")
        if story_id in str(image)
    ] or []
    # find the audio file directory for the uuid in the storyboard/audio/ directory
    audio_dir = next(
        f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/audio/{_}"
        for _ in os.listdir("storyboard/audio")
        if story_id in _
    )
    audio_files = [
        audio for audio in os.listdir(audio_dir) if audio.endswith(".mp3")
    ] or []
    # find the video file directory for the uuid in the storyboard/video/ directory
    try:
        video_dir = next(
            f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/video/{_}"
            for _ in os.listdir("storyboard/video")
            if story_id in _
        )
        video_files = [
            video for video in os.listdir(video_dir) if video.endswith(".mp4")
        ] or []
    except Exception:
        video_files = []
    # find the final video file for the uuid in the storyboard/final_video/ directory
    final_video = f"/Users/joshwren/Code/playground/stable-diffusion/storyboard/final_video/{story_id}/{story_id}.mp4"
    print(final_video)
    all_images(images)
    return StoryBoard(
        id=story_id,
        audio_files=audio_files,
        video_files=video_files,
        images=images,
        final_video=final_video,
        cache=cache_path,
    )


# image_08e3d70c-fa2d-4e2b-9d9c-1b1c55712e9e_08e3d70c-fa2d-4e2b-9d9c-1b1c55712e9e_image_1005
# widget to display the cached storyboards
cached_storyboards = ttk.Combobox(mainframe, values=find_cached_storyboards())
cached_storyboards.grid(column=1, row=1, sticky=(tk.W, tk.E))
# once the user selects a cached storyboard, load the storyboard object

# widget to load a cached storyboard
load_cached_storyboard = ttk.Button(mainframe, text="Load Cached Storyboard")
load_cached_storyboard.grid(column=2, row=1, sticky=tk.W)


# when load_cached_storyboard is clicked, load the storyboard object
load_cached_storyboard["command"] = load_storyboard

# display all images for the storyboard using PIL
images = []


def all_images(images):
    """
    Display all images for the storyboard using PIL.
    Args:

    Returns:

    """
    global mainframe
    image_dir = "./outputs/txt2img-samples"

    # create a PIL image object for each image
    processed_images = [
        PIL.Image.open(os.path.join(image_dir, image)) for image in images
    ]

    # create a Tkinter image object for each image
    tk_images = [PIL.ImageTk.PhotoImage(image) for image in processed_images]

    # display the images 10 at a time
    starting_index = 0
    # prevent too many files open error
    ending_index = 10 if len(tk_images) > 10 else len(tk_images)
    for image in tk_images[starting_index:ending_index]:
        # create a label for the image
        label = ttk.Label(mainframe, image=image)
        label.image = image
        label.grid(column=1, row=2, sticky=tk.W)
        # add the label to the images list
        images.append(label)

    # when the user clicks the next button, display the next 10 images
    def next_images():
        """
        Display the next 10 images.
        Args:

        Returns:

        """
        starting_index += 10
        ending_index += 10
        for image in tk_images[starting_index:ending_index]:
            # create a label for the image
            label = ttk.Label(mainframe, image=image)
            label.image = image
            label.grid(column=1, row=2, sticky=tk.W)
            # add the label to the images list
            images.append(label)

    # when the user clicks the previous button, display the previous 10 images
    def previous_images():
        """
        Display the previous 10 images.
        Args:

        Returns:

        """
        starting_index -= 10
        ending_index -= 10
        for image in tk_images[starting_index:ending_index]:
            # create a label for the image
            label = ttk.Label(mainframe, image=image)
            label.image = image
            label.grid(column=1, row=2, sticky=tk.W)
            # add the label to the images list
            images.append(label)

    # widget to display the next 10 images
    next_images = ttk.Button(mainframe, text="Next Images")
    next_images.grid(column=2, row=2, sticky=tk.W)
    # when next_images is clicked, display the next 10 images
    next_images["command"] = next_images

    # widget to display the previous 10 images
    previous_images = ttk.Button(mainframe, text="Previous Images")
    previous_images.grid(column=2, row=2, sticky=tk.W)
    # when previous_images is clicked, display the previous 10 images
    previous_images["command"] = previous_images


# widget to display the images
display_images = ttk.Button(mainframe, text="Display Images")
display_images.grid(column=2, row=2, sticky=tk.W)

# when display_images is clicked, display the images
display_images["command"] = display_images


# generate_all_models loop

root.mainloop()

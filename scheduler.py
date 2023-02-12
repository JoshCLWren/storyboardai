from redis import Redis
from rq import Queue

from constants import PROJECT_ID
from stable_diff_2 import *

if __name__ == "__main__":
    # Tell RQ what Redis connection to use
    job_q = Queue(connection=Redis())
    # clear the queue
    job_q.empty()
    # resume_batch_images
    project = Project(PROJECT_ID)
    project.load()
    for model in project.models:
        print(f"Loading model {model}...")
        cls = globals()[model]
        sd_config = project.config_class(cls)
        for image_index in project.image_indices:
            print(f"Loading image {image_index.index}...")
            print(f"Generating image for line {image_index.index} with {model}")
            if prompt := open(
                f"{project.output_folder}/{image_index.index}/{image_index.index}_prompt.txt",
                "r",
            ).read():
                print(f"Prompt Found: {prompt}")
                folder_path = f"{project.output_folder}/{image_index.index}/{model}"
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                filename = f"{image_index.index}.png"
                job_q.enqueue(queued_txt2img, prompt, model, folder_path, filename)

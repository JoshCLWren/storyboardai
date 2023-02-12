from redis import Redis
from rq import Queue

from stable_diff_2 import count_words_at_url, print_image

if __name__ == "__main__":
    # Tell RQ what Redis connection to use
    q = Queue(connection=Redis())
    # clear the queue
    q.empty()
    # queue the job, keep in mind that the function must be importable and keyword arguments must be serializable
    # and passed as keyword arguments like:

    image_path = "outputs/33527d88-636b-4833-876d-6d0665d970b5/0/backup_0_1/StableDiffusionV1/0.png"
    q.enqueue(print_image, image_path)

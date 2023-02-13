import random

import models
from stable_diffusers import *


def menu():
    """
    Print a menu of options for each of the methods in this file allowing the script to be run from the command line
    user may the corresponding number to run the method
    """
    print("1. batch_generate_images")
    print("2. resume_batch_images")
    print("3. from_single_prompt")
    print("4. delete_filtered_images")
    print("5. regenerate_image")
    print("6. paginated_images")
    print("7. print_image")
    print("8. exit")
    selection = input("Enter selection: ")
    if selection == "1":
        prompt_path = get_prompt_path()
        models = get_models()
        batch_generate_images(prompt_path, models)
    elif selection == "2":
        input_project_id = get_id_input()
        resume_batch_images(input_project_id)
    elif selection == "3":
        print("Enter prompt: ")
        user_prompt = input()
        from_single_prompt(user_prompt)
    elif selection == "4":
        input_project_id = get_id_input()
        delete_filtered_images(input_project_id)
    elif selection == "5":
        input_project_id = get_id_input()
        image_index = get_image_index(input_project_id)
        indexes_model = get_indexes_model(input_project_id, image_index)
        prompt_prefix, prompt_suffix = get_prompt_prefix_suffix(
            project_id=input_project_id, image_index=image_index
        )
        regenerate_image(
            input_project_id,
            image_index,
            indexes_model,
            prompt_prefix,
            prompt_suffix,
        )
    elif selection == "6":
        input_project_id = get_id_input()
        print(paginated_images(0, 10, input_project_id, "StableDiffusionV1"))
    elif selection == "7":
        image_path = get_image_path()
        print_image(
            image_path,
        )
    elif selection == "8":
        exit()
    else:
        print("Invalid selection")
    menu()


def get_id_input():
    print("Enter project id or press enter to use default")
    return (
        user_project_id
        if (user_project_id := input())
        else "33527d88-636b-4833-876d-6d0665d970b5"
    )


def get_image_path():
    print("Enter image path or press enter to use default")
    return (
        user_image_path
        if (user_image_path := input())
        else "outputs/33527d88-636b-4833-876d-6d0665d970b5/9/StableDiffusionV1/9.png"
    )


def get_prompt_path():
    print("Enter prompt path or press enter to use default")
    return (
        user_prompt_path if (user_prompt_path := input()) else "input/prison_full.txt"
    )


def get_models():
    print("Models to choose from")
    index = 1
    display_models = {
        index + 1: model.__name__ for index, model in enumerate(models.DEFAULT_MODELS)
    }
    for key, value in display_models.items():
        print(f"{key}: {value}")
    print(f"{index + 1}: All Models")
    users_models = {}
    while True:
        print("Current Chosen Models:")
        if users_models:
            for key, value in users_models.items():
                print(f"{key}: {value}")
        else:
            print("None")
        print(
            "Enter the number of the model you want to add or remove from available and your models, or press enter to finish"
        )
        if display_models:
            print("0: All Models")
            for key, value in display_models.items():
                print(f"{key}: {value}")
            try:
                user_input = input()
                if user_input.lower() in ["", " ", "q", "quit", "x", "exit"]:
                    break
                user_input = int(user_input)
            except ValueError:
                print("Invalid input, try again")
                continue
            if user_input in users_models:
                # add the model back to the dict of models to choose from
                display_models[user_input] = users_models.pop(user_input)
            if user_input == 0:
                users_models |= display_models
                display_models = {}
            if user_input not in display_models:
                print("Invalid input, try again")
                continue
            users_models[user_input] = display_models.pop(user_input)
            # remove the model from the dict of models to choose from
        else:
            print("Looks like you've chosen all the models")
            break

    return list(users_models)


def get_image_index(project_id, page=1, next_page=True):
    print("Enter image index or press enter to use default")
    while True:
        print(
            f"Current image indices page {page}: ",
        )
        images = paginated_images(
            page,
            10,
            project_id,
        )
        if len(images) < 10:
            next_page = False
        for index, image in enumerate(images):
            print(f"{index}: {image.prompt_line}")

        while next_page:
            print("Enter the index of the image you want to regenerate")
            print("Or press enter to go to the next page")
            index_input = input()
            if not index_input:
                page += 1
            try:
                index_input = int(index_input)
                if index_input in range(len(images)):
                    return index_input
            except ValueError:
                print("Invalid input, try again")

        if not next_page:
            print("Looks like you've reached the end of the list")
            print("Enter the index of the image you want to regenerate")
            print("or press enter to start over")
            index_input = input()
            if index_input == "":
                page = 0
                next_page = True
            try:
                index_input = int(index_input)
                if index_input in range(len(images)):
                    return index_input
            except ValueError:
                print("Invalid input, try again")


def get_indexes_model(project_id, image_index):
    print("Checking models for image..")

    # find the path of the image and list any model directory names that have an image in them
    project_path = f"outputs/{project_id}/{image_index}"
    index_path_contents = [m for m in os.listdir(project_path)]
    model_dirs = [stable for stable in index_path_contents if "Stable" in stable]
    available_models = {}
    for index, model_dir in enumerate(model_dirs):
        model_dir_path = os.path.join(project_path, model_dir)
        if _model_dir_contents := os.listdir(model_dir_path):
            available_models[index] = model_dir
    if not available_models:
        print("No models found")
        return None
    if len(available_models) == 1:
        return list(available_models.values())[0]
    print("Available models: ")
    for model_index, model in available_models.items():
        print(f"{model_index}: {model}")
    print("Enter model name or press enter to use default of StableDiffusionV1")
    model_input = input()
    while model_input:
        try:
            model_input = int(model_input)
            if available_models[model_input] in available_models:
                return available_models[model_input]
        except ValueError:
            print("Invalid model selection")
    return "StableDiffusionV1"


def get_prompt(project_id, image_index):
    # find the {image_index}_prompt.txt file in the project directory in the image index directory
    project_path = f"outputs/{project_id}/{image_index}"
    prompt_path = f"{project_path}/{image_index}_prompt.txt"
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            return f.read()


def get_prompt_prefix_suffix(project_id, image_index):
    current_prompt = get_prompt(project_id, image_index)
    print(f"Current prompt: {current_prompt}")
    prefix_input = ask_for_random(
        "prefix", constants.PROMPT_PREFIX_IDEAS, current_prompt
    )
    suffix_input = ask_for_random(
        "suffix", constants.PROMPT_SUFFIX_IDEAS, current_prompt
    )
    return prefix_input, suffix_input


def ask_for_random(fragment_type, fragment, current_prompt):
    print(
        f"Enter the {fragment_type} of the prompt you want to use or press enter to not add one?",
    )
    print(
        f"Or... do you want to randomly generate a {fragment_type}? (y/n)",
    )
    result = input()
    if result == "y":
        while True:
            result = random.choice(fragment)
            if fragment_type == "prefix":
                print(f"Do you approve this preview: {result} {current_prompt} y/n?")
            else:
                print(f"Do you approve this preview: {current_prompt} {result} y/n?")
            result_approved = input()
            if result_approved == "y":
                return result
            print("Ok, let's try again")
            continue
    if not result:
        result = ""
    return result


if __name__ == "__main__":
    menu()

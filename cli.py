from stable_diff_2 import *


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
        prompt_prefix, prompt_suffix = get_prompt_prefix_suffix()
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
    print("Which Models shale we use?")
    print(
        f"Models to choose from: {[[index, model] for index, model in enumerate(constants.DefaultModels)]}"
    )
    print("shall we use all models? (y/n)")
    if input() == "y":
        return constants.DefaultModels
    users_models = {}
    display_models = [constants.DefaultModels]
    while True:
        print("Current Chosen Models: ", users_models)
        print(
            "Enter the number of the model you want to add to the list, or press enter to finish"
        )
        user_input = input()
        if display_models:
            for index, model in enumerate(display_models):
                print(f"{index}: {model}")
                if user_input == str(index):
                    users_models.append(model)
                    display_models.pop(index)
                if user_input == "":
                    break
        else:
            print("Looks like you've chosen all the models")
            break

    return list(users_models)


def get_image_index(project_id):
    print("Enter image index or press enter to use default")
    page = 1
    while True:
        print(
            f"Current image indices page {page}: ",
        )
        images = paginated_images(
            page,
            10,
            project_id,
        )
        print(images)
        print("Enter the index of the image you want to regenerate")
        print("Or press enter to go to the next page")
        index_input = input()
        if index_input == "":
            page += 1
        elif index_input in images:
            return index_input
        else:
            break


def get_indexes_model(project_id, image_index):
    print("Enter model name or press enter to use default of StableDiffusionV1")
    # find the path of the image and list any model directory names that have an image in them
    project_path = f"outputs/{project_id}/{image_index}"

    available_models = [
        model
        for model in os.listdir(project_path)
        if model in models.DEFAULT_MODELS
        and os.path.exists(f"{project_path}/{model}/{image_index}.png")
    ]
    print("Available models: ")
    for model_index, model in enumerate(available_models):
        print(f"{model_index}: {model}")
    print("Enter the number of the model you want to regenerate or press enter to exit")
    model_input = input()
    if available_models[model_input] in available_models:
        return available_models[model_input]
    if model_input == "":
        return None
    print("Invalid model selection")
    return get_indexes_model(project_id, image_index)


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
            print(f"Do you like: {result} {current_prompt} y/n?")
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

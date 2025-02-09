import os
import cv2
import gradio as gr
import numpy as np
import random
import base64
import requests
import json
import time

# Function to handle the virtual try-on process
def tryon(person_img, garment_img, seed, randomize_seed):
    post_start_time = time.time()
    
    # Check if the required images are provided
    if person_img is None or garment_img is None:
        return None, None, "Empty image"

    # Randomize seed if the option is selected
    if randomize_seed:
        seed = random.randint(0, MAX_SEED)

    # Encode person and garment images as base64 strings
    encoded_person_img = cv2.imencode('.jpg', cv2.cvtColor(person_img, cv2.COLOR_RGB2BGR))[1].tobytes()
    encoded_person_img = base64.b64encode(encoded_person_img).decode('utf-8')
    
    encoded_garment_img = cv2.imencode('.jpg', cv2.cvtColor(garment_img, cv2.COLOR_RGB2BGR))[1].tobytes()
    encoded_garment_img = base64.b64encode(encoded_garment_img).decode('utf-8')

    # Define API URL and headers for the POST request
    url = "http://" + os.environ['tryon_url'] + "Submit"
    token = os.environ['token']
    cookie = os.environ['Cookie']
    referer = os.environ['referer']
    headers = {'Content-Type': 'application/json', 'token': token, 'Cookie': cookie, 'referer': referer}
    
    # Prepare the data to send in the request
    data = {
        "clothImage": encoded_garment_img,
        "humanImage": encoded_person_img,
        "seed": seed
    }

    try:
        # Send the POST request to submit the try-on task
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=50)
        print("post response code", response.status_code)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            result = response.json()['result']
            status = result['status']

            # If the status is success, retrieve the unique task ID
            if status == "success":
                uuid = result['result']
                print(uuid)
    except Exception as err:
        print(f"Error: {err}")
        raise gr.Error("Too many users, please try again later")

    post_end_time = time.time()
    print(f"post time used: {post_end_time-post_start_time}")

    # Start polling the server for the result
    get_start_time = time.time()
    time.sleep(9)  # Initial wait to give the server time to process
    Max_Retry = 10
    result_img = None

    for i in range(Max_Retry):
        try:
            # Send GET request to check the task status
            url = "http://" + os.environ['tryon_url'] + "Query?taskId=" + uuid
            response = requests.get(url, headers=headers, timeout=15)
            print("get response code", response.status_code)

            # Check if the GET request was successful
            if response.status_code == 200:
                result = response.json()['result']
                status = result['status']

                # If the status is success, decode the result image
                if status == "success":
                    result = base64.b64decode(result['result'])
                    result_np = np.frombuffer(result, np.uint8)
                    result_img = cv2.imdecode(result_np, cv2.IMREAD_UNCHANGED)
                    result_img = cv2.cvtColor(result_img, cv2.COLOR_RGB2BGR)
                    info = "Success"
                    break
                elif status == "error":
                    raise gr.Error("Too many users, please try again later")
            else:
                print(response.text)
                info = "URL error, please contact the admin"
        except requests.exceptions.ReadTimeout:
            print("timeout")
            info = "Too many users, please try again later"
        except Exception as err:
            print(f"Error: {err}")

        time.sleep(1)  # Retry delay

    get_end_time = time.time()
    print(f"get time used: {get_end_time-get_start_time}")

    return result_img, seed, info

# Function to start the try-on process (alternative method)
def start_tryon(person_img, garment_img, seed, randomize_seed):
    start_time = time.time()

    # Check if the required images are provided
    if person_img is None or garment_img is None:
        return None, None, "Empty image"

    # Randomize seed if the option is selected
    if randomize_seed:
        seed = random.randint(0, MAX_SEED)

    # Encode person and garment images as base64 strings
    encoded_person_img = cv2.imencode('.jpg', cv2.cvtColor(person_img, cv2.COLOR_RGB2BGR))[1].tobytes()
    encoded_person_img = base64.b64encode(encoded_person_img).decode('utf-8')

    encoded_garment_img = cv2.imencode('.jpg', cv2.cvtColor(garment_img, cv2.COLOR_RGB2BGR))[1].tobytes()
    encoded_garment_img = base64.b64encode(encoded_garment_img).decode('utf-8')

    # Define API URL and headers for the POST request
    url = "http://" + os.environ['tryon_url']
    token = os.environ['token']
    cookie = os.environ['Cookie']
    referer = os.environ['referer']
    headers = {'Content-Type': 'application/json', 'token': token, 'Cookie': cookie, 'referer': referer}

    # Prepare the data to send in the request
    data = {
        "clothImage": encoded_garment_img,
        "humanImage": encoded_person_img,
        "seed": seed
    }

    result_img = None
    try:
        # Send the POST request to the try-on API
        session = requests.Session()
        response = session.post(url, headers=headers, data=json.dumps(data), timeout=60)
        print("response code", response.status_code)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            result = response.json()['result']
            status = result['status']

            # If the status is success, decode the result image
            if status == "success":
                result = base64.b64decode(result['result'])
                result_np = np.frombuffer(result, np.uint8)
                result_img = cv2.imdecode(result_np, cv2.IMREAD_UNCHANGED)
                result_img = cv2.cvtColor(result_img, cv2.COLOR_RGB2BGR)
                info = "Success"
            else:
                info = "Try again later"
        else:
            print(response.text)
            info = "URL error, please contact the admin"
    except requests.exceptions.ReadTimeout:
        print("timeout")
        info = "Too many users, please try again later"
        raise gr.Error("Too many users, please try again later")
    except Exception as err:
        print(f"Error: {err}")
        info = "Error, please contact the admin"

    end_time = time.time()
    print(f"time used: {end_time-start_time}")

    return result_img, seed, info

# Maximum value for seed
MAX_SEED = 999999

# Load example images for demonstration
example_path = os.path.join(os.path.dirname(__file__), 'assets')
garm_list = os.listdir(os.path.join(example_path, "cloth"))
garm_list_path = [os.path.join(example_path, "cloth", garm) for garm in garm_list]
human_list = os.listdir(os.path.join(example_path, "human"))
human_list_path = [os.path.join(example_path, "human", human) for human in human_list]

# CSS for customizing the Gradio interface
css="""
#col-left {
    margin: 0 auto;
    max-width: 430px;
}
#col-mid {
    margin: 0 auto;
    max-width: 430px;
}
#col-right {
    margin: 0 auto;
    max-width: 430px;
}
#col-showcase {
    margin: 0 auto;
    max-width: 1100px;
}
#button {
    color: blue;
}
"""

# Load description content from a file
def load_description(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

# Function to switch images (utility function)
def change_imgs(image1, image2):
    return image1, image2

# Define the Gradio Blocks interface
with gr.Blocks(css=css) as Tryon:
    # Instructions for the steps
    with gr.Row():
        with gr.Column(elem_id="col-left"):
            gr.HTML("""
            <div style="display: flex; justify-content: center; align-items: center; text-align: center; font-size: 20px;">
                <div>
                Step 1.  Upload a person image ⬇️
                </div>
            </div>
            """)
        with gr.Column(elem_id="col-mid"):
            gr.HTML("""
            <div style="display: flex; justify-content: center; align-items: center; text-align: center; font-size: 20px;">
                <div>
                Step 2. Upload a garment image ⬇️
                </div>
            </div>
            """)
        with gr.Column(elem_id="col-right"):
            gr.HTML("""
            <div style="display: flex; justify-content: center; align-items: center; text-align: center; font-size: 20px;">
                <div>
                Step 3. Press “Run” to get try-on results
                </div>
            </div>
            """)

    # Input sections for uploading images
    with gr.Row():
        with gr.Column(elem_id="col-left"):
            imgs = gr.Image(label="Person image", sources='upload', type="numpy")
            example = gr.Examples(
                inputs=imgs,
                examples_per_page=12,
                examples=human_list_path
            )
        with gr.Column(elem_id="col-mid"):
            garm_img = gr.Image(label="Garment image", sources='upload', type="numpy")
            example = gr.Examples(
                inputs=garm_img,
                examples_per_page=12,
                examples=garm_list_path
            )
        with gr.Column(elem_id="col-right"):
            image_out = gr.Image(label="Result", show_share_button=False)
            with gr.Row():
                seed = gr.Slider(
                    label="Seed",
                    minimum=0,
                    maximum=MAX_SEED,
                    step=1,
                    value=0,
                )
                randomize_seed = gr.Checkbox(label="Random seed", value=True)
            with gr.Row():
                seed_used = gr.Number(label="Seed used")
                result_info = gr.Text(label="Response")
            test_button = gr.Button(value="Run", elem_id="button")

    # Define button click functionality
    test_button.click(fn=tryon, inputs=[imgs, garm_img, seed, randomize_seed], outputs=[image_out, seed_used, result_info], api_name='tryon', concurrency_limit=40)

    # Example showcase section
    with gr.Column(elem_id="col-showcase"):
        gr.HTML("""
        <div style="display: flex; justify-content: center; align-items: center; text-align: center; font-size: 20px;">
            <div> </div>
            <br>
            <div>
            Virtual try-on examples in pairs of person and garment images
            </div>
        </div>
        """)
        show_case = gr.Examples(
            examples=[
                ["assets/examples/model2.png", "assets/examples/garment2.png", "assets/examples/result2.png"],
                ["assets/examples/model3.png", "assets/examples/garment3.png", "assets/examples/result3.png"],
                ["assets/examples/model1.png", "assets/examples/garment1.png", "assets/examples/result1.png"],
            ],
            inputs=[imgs, garm_img, image_out],
            label=None
        )

# Launch the Gradio interface
Tryon.launch()

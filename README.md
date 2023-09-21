# livestream-ai-worker

This is a Python application that applies AI to a livestream.

## Getting Started

To get started with this project, follow these steps:

1. Clone the repository to your local machine.
2. Install the required dependencies using pip.
3. Run the application using the command `python app.py`.

## Dependencies

This project requires the following dependencies:

- Python 3.x
- [List any additional dependencies here]


## Run locally

### Requirements
- CUDA 12.1 for x86_64
- Nvidia GPU (RTX2080/RTX3080/T4/A100)
- DeepStream SDK 6.3 (for DeepStream extensions)


### Environment setup

#### Python venv
```
python -m venv venv
source ./venv/bin/activate
```
#### Gstreamer
```sh
sudo apt install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl \
    gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio
```
#### GST Python bindings
```sh
sudo apt install python3-gi python3-dev python3-gst-1.0 python-gi-dev git python-dev \
    python3 python3-pip python3.8-dev cmake g++ build-essential libglib2.0-dev \
    libglib2.0-dev-bin libgstreamer1.0-dev libtool m4 autoconf automake libgirepository1.0-dev libcairo2-dev
```
#### Deep Stream
- Install deep stream as described [here](https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_Quickstart.html) 
- Download and install ds python bindings
```sh
curl -O -L https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v1.1.6/pyds-1.1.6-py3-none-linux_x86_64.whl
pip3 install ./pyds-1.1.6-py3-none-linux_x86_64.whl;
```

#### Maxine
- TBD

## Usage

To use this application, follow these steps:

1. TBD

## Contributing

If you would like to contribute to this project, please follow these steps:

1. Create a new branch for your changes.
2. Make your changes and commit them.
4. Push your changes to your branch.
5. Submit a merge request.

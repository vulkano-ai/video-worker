ARG BASE_IMAGE=nvcr.io/nvidia/deepstream:6.2-devel
FROM ${BASE_IMAGE}
ARG GL_TOKEN
ARG ENVIRONMENT

ENV ENVIRONMENT=$ENVIRONMENT
ENV DEBIAN_FRONTEND noninteractive

ENV NVIDIA_DRIVER_CAPABILITIES $NVIDIA_DRIVER_CAPABILITIES,video
ENV LOGLEVEL="INFO"
ENV GST_DEBUG=2


RUN apt update -y  && apt upgrade -y

# GStreamer Dependencies
RUN apt install -y libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-x gstreamer1.0-alsa gstreamer1.0-gl \
    gstreamer1.0-gtk3 gstreamer1.0-qt5 gstreamer1.0-pulseaudio

# Gst RTSP Server
RUN apt install -y libgstrtspserver-1.0-dev gstreamer1.0-rtsp

# Deepstream Dependencies
RUN apt install -y python3-gi python3-dev python3-gst-1.0 python-gi-dev git python-dev \
    python3 python3-pip python3.8-dev cmake g++ build-essential libglib2.0-dev \
    libglib2.0-dev-bin libgstreamer1.0-dev libtool m4 autoconf automake libgirepository1.0-dev libcairo2-dev

# Clone the Deepstream Python Apps Repo into <deepstream>/sources
WORKDIR /opt/nvidia/deepstream/deepstream/sources
RUN git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git

# Download and install the Deepstream Python Bindings
RUN mkdir /opt/nvidia/deepstream/deepstream/sources/deepstream_python_apps/bindings/build
WORKDIR /opt/nvidia/deepstream/deepstream/sources/deepstream_python_apps/bindings/build

RUN curl -O -L https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/releases/download/v1.1.6/pyds-1.1.6-py3-none-linux_x86_64.whl && \
    pip3 install ./pyds-1.1.6-py3-none-linux_x86_64.whl;

ENV CUDA_VER 11.8

# nvdsinfer_custom_impl_Yolo
WORKDIR /tmp

RUN git clone https://github.com/marcoslucianops/DeepStream-Yolo.git

RUN cd DeepStream-Yolo/nvdsinfer_custom_impl_Yolo/ && \
    make -j$(nproc) && \
    cp libnvdsinfer_custom_impl_Yolo.so /usr/local/lib/libnvdsinfer_yolo_v8.so  && \
    cd ../ && rm -rf DeepStream-Yolo

COPY . /opt/app

WORKDIR /opt/app

RUN pip install -r requirements.txt --extra-index-url https://__token__:$GL_TOKEN@gitlab.com/api/v4/groups/park-smart/-/packages/pypi/simple


CMD ["/usr/bin/python3", "app.py"]
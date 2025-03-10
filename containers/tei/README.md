# Text Embeddings Inference (TEI) Containers

[Text Embeddings Inference](https://github.com/huggingface/text-embeddings-inference) is a toolkit for deploying and serving open source text embeddings and sequence classification models developed by Hugging Face. TEI is a blazing fast inference solution that enables high-performance extraction for the most popular models, including FlagEmbedding, Ember, GTE and E5.

## Published Containers

To check which of the available Hugging Face DLCs are published, you can either check the [Google Cloud Deep Learning Containers Documentation for TEI](https://cloud.google.com/deep-learning-containers/docs/choosing-container#text-embeddings-inference), the [Google Cloud Artifact Registry](https://console.cloud.google.com/artifacts/docker/deeplearning-platform-release/us/gcr.io) or use the `gcloud` command to list the available containers with the tag `huggingface-text-embeddings-inference` as follows:

```bash
gcloud container images list --repository="us-docker.pkg.dev/deeplearning-platform-release/gcr.io" | grep "huggingface-text-embeddings-inference"
```

## Getting Started

Below you will find the instructions on how to run and test the TEI containers available within this repository. Note that before proceeding you need to first ensure that you have Docker installed either on your local or remote instance, if not, please follow the instructions on how to install Docker [here](https://docs.docker.com/get-docker/).

Additionally, if you're willing to run the Docker container in GPUs you need to ensure that your hardware is supported (NVIDIA drivers on your device need to be compatible with CUDA version 12.2 or higher) and also install the NVIDIA Container Toolkit.

To find the supported models and hardware before running the TEI images, feel free to check [TEI's documentation](https://huggingface.co/docs/text-embeddings-inference/supported_models).

### Run

To run this DLC, you need to first define the model to deploy i.e. any model from the Hugging Face Hub that contains the tag `text-embeddings-inference` which means that it's supported by TEI; to explore all the available models within the Hub, please check [here](https://huggingface.co/models?other=text-embeddings-inference&sort=trending).

Besides selecting which model to deploy, to take into consideration that TEI supports the following models:

- **Text Embeddings**: these are models are pre-trained models that convert text into numerical vectors, which can be used for a variety of downstream tasks.

- **Re-Rankers**: these models are sequence classification cross-encoders models with a single class that scores the similarity between a query and a text.

- **Sequence Classification**: these models are classic sequence classification models as e.g. BERT, RoBERTa, etc.

Then eady to run the container depending on the accelerator to use as follows:

- **CPU**: To run the image on a CPU instance, you need to provide the `MODEL_ID` environment variable and expose the port 8080.

  ```bash
  docker run -ti -p 8080:8080 \
      -e MODEL_ID=BAAI/bge-large-en-v1.5 \
      us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-text-embeddings-inference-cpu.1.4.0
  ```

- **GPU**: To run the image on a GPU instance, you need to also add `--gpus all` so that the container can access the GPUs, and then provide the `MODEL_ID` environment variable and expose the port 8080.

  ```bash
  docker run -ti --gpus all -p 8080:8080 \
      -e MODEL_ID=BAAI/bge-large-en-v1.5 \
      us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-text-embeddings-inference-gpu.1.4.0
  ```

### Test

Once the Docker container is running, as it has been deployed with `text-embeddings-router`, the API will expose the following endpoints listed within the [TEI OpenAPI Specification](https://huggingface.github.io/text-embeddings-inference/).

> [!WARNING]
> Even though the different endpoints are listed below, take into consideration that not every TEI supported model supports those endpoints, since those models are different, and even if the endpoints are exposed, you should only used the endpoint for which the model you are deploying is suited for. For example, since above you're deploying the `BAAI/bge-large-en-v1.5` model, you should only use the `/embed` endpoint.

Depending on the model that has been deployed the inference endpoints will be:

- `/embed`: generates the embeddings for the input text.

  ```bash
  curl 0.0.0.0:8080/embed \
      -X POST \
      -d '{"inputs":"Deep Learning is a"}' \
      -H 'Content-Type: application/json'
  ```

- `/rerank`: ranks the similarity between a query and a list of texts.

  ```bash
  curl 0.0.0.0:8080/rerank \
      -X POST \
      -d '{"query":"Deep Learning is a","texts":["Machine Learning is a","Deep Learning is a","Deep Learning is a subset of Machine Learning"]}' \
      -H 'Content-Type: application/json'
  ```

- `/predict`: predicts the class of the input text.

  ```bash
  curl 0.0.0.0:8080/predict \
      -X POST \
      -d '{"inputs":"Deep Learning is a subset of Machine Learning"}' \
      -H 'Content-Type: application/json'
  ```

> [!NOTE]
> Additionally, note that both `/embed` for text embeddings models and `/predict` for sequence classification models support batching so that instead of a single instance with `inputs` being a string, a `List[str]` can be provided instead.

## Advanced

### Build

> [!WARNING]
> Building the containers is not recommended since those are already built by Hugging Face and Google Cloud teams and provided openly, so the recommended approach is to use the pre-built containers available in [Google Cloud's Artifact Registry](https://console.cloud.google.com/artifacts/docker/deeplearning-platform-release/us/gcr.io) instead.

Since TEI comes with two different containers depending on the accelerator used for the inference, being either CPU or GPU, those have different constraints when building the Docker image as described below:

- **CPU**: To build TEI for CPU, you will need an instance with enough CPU RAM, but most instances should be able to successfully build the CPU image since it's not too memory-intensive.

  ```bash
  docker build -t us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-text-embeddings-inference-cpu.1.4.0 -f containers/tei/cpu/1.4.0/Dockerfile .
  ```

- **GPU**: To build TEI for GPU, you will need an instance with at least 4 NVIDIA GPUs available with at least 24 GiB of VRAM each, since TEI, similarly to TGI, needs to build and compile the kernels required for the optimized inference. Also note that the build process may take ~15 minutes to complete, depending on the instance's specifications.

  ```bash
  docker build -t us-docker.pkg.dev/deeplearning-platform-release/gcr.io/huggingface-text-embeddings-inference-gpu.1.4.0 -f containers/tei/gpu/1.4.0/Dockerfile .
  ```

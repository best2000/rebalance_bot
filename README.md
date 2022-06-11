# Instructions

### 1. Edit config.ini

- edit bot parameters in `config.ini`

### 2. Edit Dockerfile

- edit ENV with your `API_KEY` and `SECRET_KEY`

### 3. Start running bot
```shell
#build docker image
docker build -t <name>:<tag> .
#run container from image, interactive mode, auto delete
docker run -it --rm <imageId>
```
- check host mapped volume for linux at /var/lib/docker/volumes/
 - for windows at \\wsl$\docker-desktop-data\version-pack-data\community\docker\volumes 
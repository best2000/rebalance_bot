# Instructions

### 1. Edit config.ini

- edit parameters in `/public/config.ini`
- or edit it later, inside container

### 2. Edit `Dockerfile`

- edit ENV with your `API_KEY` and `SECRET_KEY`
- or add ENV later, inside container

### 3. Start running bot
```shell
#build docker image
docker build -t <name>:<tag> .
#run container from image, interactive mode, auto delete, mapped host volume to check log data
docker run --name <container_name> -it -v <hostPath>:/app/public <imageId> bash
```
```shell
#inside container shell
python main.py
```
- check host mapped volume for linux(default) at /var/lib/docker/volumes/
- for windows(default) at \\wsl$\docker-desktop-data\version-pack-data\community\docker\volumes 
- To get back in the container shell run this command
```shell
docker exec -it <container_id> bash
```

### 3. Check bot status
- all the logs and others is in the `/public` folder of container which is already mapped to your host system
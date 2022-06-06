# Instructions

### 1. Edit config.ini

- edit bot parameters in `config.ini`
- change testnet to `0` if you want real account

### 2. Edit Dockerfile

- edit ENV with your `API_KEY` and `SECRET_KEY`

### 3. Start running bot
```shell
#build docker image
docker build -t <name>:<tag> .
#run container from image, interactive mode, auto delete, mapped host volume to check log data
docker run -it --rm -v <hostDirectoryName>:/app/public <imageId>
```

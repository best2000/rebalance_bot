#Instruction
##1.Edit config.ini
edit bot parameters in config.ini
##2.Run docker
```shell
#build docker image
docker build -t <name>:<tag>
#run container from image, interactive mode, auto delete 
docker run --it --rm <imageId>
```
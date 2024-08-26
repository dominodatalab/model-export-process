# Remove stopped containers
docker container prune -f

# Remove unused images
docker image prune -a -f

# Remove unused volumes
docker volume prune -f

# Remove unused networks
docker network prune -f

# Remove all unused objects (containers, networks, images, and volumes)
docker system prune -a -f --volume
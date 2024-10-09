# Recipes for building ubuntu images.  

.PHONY:
shell:
	sudo docker compose -f "./dockers/docker-compose.yml" run ubuntu_shell_2204 
	
.PHONY:
shell_build:
	sudo docker compose  -f "./dockers/docker-compose.yml"  build ubuntu_shell_2204

.PHONY:
jupy_build:
	sudo docker compose -f "./dockers/docker-compose.yml" build jupy

.PHONY:
jupy:
		sudo docker compose -f "./dockers/docker-compose.yml" run -p 8889:8889 jupy

.PHONY:
red:
	sudo docker compose -f "./dockers/docker-compose.yml" up red

.PHONY:
red_build:
	sudo docker compose -f "./dockers/docker-compose.yml" build red



.PHONY:
api_build:
	sudo docker compose -f "./dockers/docker-compose.yml" build api

.PHONY:
api:
		sudo docker compose -f "./dockers/docker-compose.yml" run -p 8000:8000 api

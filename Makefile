# Recipes for building ubuntu images.  

.PHONY:
shell:
	docker compose -f "./dockers/docker-compose.yml" run ubuntu_shell_2204 
	
.PHONY:
shell_build:
	docker compose  -f "./dockers/docker-compose.yml"  build ubuntu_shell_2204

.PHONY:
jupy_build:
	docker compose -f "./dockers/docker-compose.yml" build jupy

.PHONY:
jupy:
	docker compose -f "./dockers/docker-compose.yml" run -p 8889:8889 jupy

.PHONY:
red:
	docker compose -f "./dockers/docker-compose.yml" up red

.PHONY:
red_build:
	docker compose -f "./dockers/docker-compose.yml" build red



.PHONY:
api_build:
	docker compose -f "./dockers/docker-compose.yml" build api

.PHONY:
api:
	docker compose -f "./dockers/docker-compose.yml" run -p 8000:8000 api

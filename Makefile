# Cleanup
clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +
	rm -rf .cache

clean_vscode:
	rm -rf .vscode

clean_pypi:
	rm -rf dist
	rm -rf epages_rest_python.egg-info

clean_all: clean clean_vscode clean_pypi

# Docker
docker_build:
	docker build -t oozz/epages-beyond-app:latest .

docker_run:
	docker run --env-file ./env.list --network="host" -it oozz/epages-beyond-app:latest

docker_buildrun: docker_build docker_run

docker_clean:
	docker ps -q -f status=exited | xargs --no-run-if-empty docker rm
	docker images -q -f dangling=true | xargs --no-run-if-empty docker rmi

docker_push:
	docker push oozz/epages-beyond-app

docker_init_env:
	cp env.list.template env.list

.PHONY: clean clean_vscode clean_pypi clean_all \
docker_build docker_run \
docker_buildrun \
docker_clean docker_push docker_init_env

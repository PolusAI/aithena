# aithena

Aithena is the umbrella repository for all aithena projects.
It contains services, agents, apps and third party software
that are used to build ai services.

## docker images

For testing purpose, you can modify the org to tag images with using
the `DOCKER_ORG` env variable.

ex:
```shell
DOCKER_ORG=my_personal_registry ./build-docker.sh
```

### [Currently Disabled]

We are shipping multi-platform container images.
We are using containerd to achieve that. 
To install containerd on osx, install the docker desktop app.
Go to general setting, beta features and select `use containerd`.

To deploy containers without this experimental feature, go to each
./build-docker.sh script and update the `docker build` instruction acccordingly.
# Project Setup

This project uses Docker and Docker Compose to deploy

## Setup

1. Clone the repository

```bash
git clone https://bitbucket.org/Panfillich/training/src/KAN-4/
```

2. Generate requirements files

```bash
docker compose run --rm pip-compile
```

## Running Containers

1. To launch the tests use the command:

```bash
docker compose run fastapi-tests
```

2. To run pre-commit hooks inside the container use these commands:

```bash
docker compose run --rm pre-commit
```

3. Start the app using Docker Compose

```bash
docker compose up fastapi
```

4. The application will be available at [http://localhost:8000]

## Logging

To view logs from all containers use the command:

```bash
docker compose logs -f
```

## Stopping Containers

To stop the containers use the command:

```bash
docker compose down
```


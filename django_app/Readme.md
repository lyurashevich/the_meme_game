# Project Setup

This project uses Docker and Docker Compose to deploy

## Setup

1. Clone the repository

```bash
git clone https://bitbucket.org/Panfillich/training/src/KAN-3/
```

2. (Optional) Create a `.env` file based on the `.env.example`:

```bash
cp env.example .env
```

3. Generate requirements files

```bash
docker compose run --rm pip-compile
```

## Running Containers

1. To run the tests use the command:

```bash
docker compose run tests
```

2. To run pre-commit inside the container use:

```bash
docker compose run --rm pre-commit
```

3. To start the container with application  using Docker Compose

```bash
docker compose up django
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


pipeline {
	agent any

	options {
		buildDiscarder(logRotator(daysToKeepStr: '1'))
	}

	stages {
		stage('Stop existing containers') {
			steps {
				sh "docker compose down"
			}
		}

		stage('Pre-commit') {
			steps {
				echo 'Running pre-commit...'
				sh "docker compose run --build pre-commit"
			}
		}

		stage('Test Django') {
			steps {
				echo 'Testing django...'
				sh "docker compose run --build tests && docker compose down -v"
			}
		}

		stage('Test FastAPI') {
			steps {
				echo 'Testing FastAPI...'
				sh "docker compose run --build fastapi-tests"
			}
		}
	}

	post {
		always {
			sh "docker compose rm -s -f -v"
			sh "docker compose ps"
		}
	}
}
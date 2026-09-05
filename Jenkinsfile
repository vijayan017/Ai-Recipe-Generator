pipeline {
    agent any

    environment {
        PYTHON = 'C:\\Users\\Vijayan\\AppData\\Local\\Python\\bin\\python.exe'
        GIT = 'C:\\Program Files\\Git\\cmd\\git.exe'

        DOCKER_IMAGE = 'vijayan12/ai-recipe-generator'
        DOCKER_HUB_USER = 'vijayan12'

        APP_NAME = 'ai-recipe-generator'
        APP_PORT = '5000'
        HOST_PORT = '5000'
    }

    stages {

        stage('Check Tools') {
            steps {
                echo 'Checking required tools...'

                bat '''
                    echo ========================================
                    echo Checking Python
                    echo ========================================
                    "%PYTHON%" --version

                    echo.
                    echo ========================================
                    echo Checking Git
                    echo ========================================
                    "%GIT%" --version

                    echo.
                    echo ========================================
                    echo Checking Docker
                    echo ========================================
                    docker --version

                    echo.
                    echo ========================================
                    echo Checking Docker Engine
                    echo ========================================
                    docker info
                '''
            }
        }

        stage('Set Up Python') {
            steps {
                echo 'Setting up Python environment...'

                bat '''
                    if not exist venv (
                        "%PYTHON%" -m venv venv
                    )

                    call venv\\Scripts\\activate.bat

                    echo Python version:
                    python --version

                    echo.
                    echo Upgrading pip:
                    python -m pip install --upgrade pip

                    echo.
                    echo Installing project dependencies:

                    if exist requirements.txt (
                        python -m pip install -r requirements.txt
                    ) else (
                        echo ERROR: requirements.txt not found.
                        exit /b 1
                    )
                '''
            }
        }

        stage('Lint / Basic Checks') {
            steps {
                echo 'Running Flake8 code checks...'

                bat '''
                    call venv\\Scripts\\activate.bat

                    python -m pip install flake8

                    echo.
                    echo ========================================
                    echo FLAKE8 RESULTS
                    echo ========================================

                    flake8 . --exclude=venv,__pycache__,.git --count --statistics

                    echo.
                    echo Flake8 completed.
                    echo Lint warnings will not stop deployment.
                    echo ========================================

                    exit /b 0
                '''
            }
        }

        stage('Run Tests') {
            steps {
                echo 'Running application tests...'

                bat '''
                    call venv\\Scripts\\activate.bat

                    python -m pip install pytest

                    echo.
                    echo ========================================
                    echo RUNNING TESTS
                    echo ========================================

                    if exist tests (
                        pytest -v

                        if errorlevel 1 (
                            echo Tests failed.
                            exit /b 1
                        )
                    ) else (
                        echo No tests directory found.
                        echo Skipping pytest.
                    )

                    echo.
                    echo Tests stage completed.
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Building Docker image...'

                bat '''
                    echo.
                    echo ========================================
                    echo BUILDING DOCKER IMAGE
                    echo ========================================

                    docker build -t %DOCKER_IMAGE%:%BUILD_NUMBER% .

                    if errorlevel 1 (
                        echo Docker build failed.
                        exit /b 1
                    )

                    docker tag %DOCKER_IMAGE%:%BUILD_NUMBER% %DOCKER_IMAGE%:latest

                    echo.
                    echo Docker build completed successfully.
                    echo Image: %DOCKER_IMAGE%:%BUILD_NUMBER%
                    echo Image: %DOCKER_IMAGE%:latest

                    docker images %DOCKER_IMAGE%
                '''
            }
        }

        stage('Login to DockerHub') {
            steps {
                script {
                    withCredentials([
                        usernamePassword(
                            credentialsId: 'dockerhub-credentials',
                            usernameVariable: 'DOCKERHUB_USER',
                            passwordVariable: 'DOCKERHUB_PASS'
                        )
                    ]) {
                        bat '''
                            echo %DOCKERHUB_PASS%| docker login -u %DOCKERHUB_USER% --password-stdin
                        '''
                    }
                }
            }
        }

        stage('Push to DockerHub') {
            steps {
                echo 'Pushing Docker image to Docker Hub...'

                bat '''
                    echo.
                    echo ========================================
                    echo PUSHING DOCKER IMAGE
                    echo ========================================

                    echo Pushing build image...
                    docker push %DOCKER_IMAGE%:%BUILD_NUMBER%

                    if errorlevel 1 (
                        echo Failed to push build image.
                        exit /b 1
                    )

                    echo.
                    echo Pushing latest image...
                    docker push %DOCKER_IMAGE%:latest

                    if errorlevel 1 (
                        echo Failed to push latest image.
                        exit /b 1
                    )

                    echo.
                    echo Docker images pushed successfully.
                    echo ========================================
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying AI Recipe Generator...'

                bat '''
                    echo.
                    echo ========================================
                    echo DEPLOYING APPLICATION
                    echo ========================================

                    echo Stopping old container...
                    docker stop %APP_NAME% >nul 2>&1

                    echo Removing old container...
                    docker rm %APP_NAME% >nul 2>&1

                    echo Pulling latest Docker image...
                    docker pull %DOCKER_IMAGE%:latest

                    if errorlevel 1 (
                        echo Failed to pull Docker image.
                        exit /b 1
                    )

                    echo Starting new container...

                    docker run -d ^
                        --name %APP_NAME% ^
                        -p %HOST_PORT%:%APP_PORT% ^
                        %DOCKER_IMAGE%:latest

                    if errorlevel 1 (
                        echo Failed to start Docker container.
                        exit /b 1
                    )

                    echo.
                    echo Container started successfully.
                    echo.

                    docker ps --filter "name=%APP_NAME%"

                    echo.
                    echo Application URL:
                    echo http://localhost:%HOST_PORT%

                    echo ========================================
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                echo 'Verifying application deployment...'

                bat '''
                    echo.
                    echo ========================================
                    echo VERIFYING DEPLOYMENT
                    echo ========================================

                    timeout /t 10 /nobreak >nul

                    echo.
                    echo Container status:
                    docker ps --filter "name=%APP_NAME%"

                    echo.
                    echo Container logs:
                    docker logs %APP_NAME% --tail 30

                    echo.
                    echo Checking application HTTP response...

                    powershell -Command "try { $response = Invoke-WebRequest -Uri http://localhost:%HOST_PORT% -UseBasicParsing -TimeoutSec 10; Write-Host ('Application HTTP Status: ' + $response.StatusCode) } catch { Write-Host ('Application check returned: ' + $_.Exception.Message) }"

                    echo.
                    echo ========================================
                    echo DEPLOYMENT VERIFICATION COMPLETED
                    echo ========================================
                '''
            }
        }
    }

    post {

        success {
            echo '========================================'
            echo 'PIPELINE COMPLETED SUCCESSFULLY'
            echo '========================================'
            echo 'AI Recipe Generator has been deployed.'
            echo 'Application URL: http://localhost:5000'
            echo 'Docker Image: vijayan12/ai-recipe-generator:latest'
            echo '========================================'
        }

        failure {
            echo '========================================'
            echo 'PIPELINE FAILED'
            echo '========================================'
            echo 'Check the Jenkins Console Output for the failed stage.'
            echo '========================================'
        }

        always {
            echo 'PIPELINE EXECUTION COMPLETED'
        }
    }
}

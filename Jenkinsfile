pipeline {
    agent { label 'agent1' } // Используем ваш агент 

    parameters {
        choice(name: 'SERVICE_TO_RUN', choices: ['AUTO', 'auth_service', 'wallet_service', 'ALL'], description: 'Что строим?')
        string(name: 'BRANCH_NAME', defaultValue: 'main', description: 'Branch to build') 
        booleanParam(name: 'RUN_QA_TESTS', defaultValue: true, description: 'Run QA Tests') 
        booleanParam(name: 'DEPLOY_TO_PROD', defaultValue: false, description: 'Deploy to Production') 
    }

    environment {
        SERVER_IP = credentials('SERVER_IP') 
        DOCKER_REGISTRY = "ghcr.io"
        DOCKER_ORG = "eugene-codx"
        // Список всех микросервисов для итерации
        ALL_SERVICES = "auth_service wallet_service"
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    // 1. Checkout 
                    checkout scm: ([$class: 'GitSCM', branches: [[name: "\$BRANCH_NAME"]], 
                        userRemoteConfigs: [[url: credentials('REPO_URL'), credentialsId: 'GITHUB_SSH_KEY']]])

                    // 2. Определяем список сервисов для работы
                    def selected = []
                    if (params.SERVICE_TO_RUN == 'AUTO') {
                        env.ALL_SERVICES.split().each { if (isFolderChanged(it)) selected.add(it) }
                    } else if (params.SERVICE_TO_RUN == 'ALL') {
                        selected = env.ALL_SERVICES.split().toList()
                    } else {
                        selected.add(params.SERVICE_TO_RUN)
                    }
                    env.TARGET_SERVICES = selected.join(' ')
                }
            }
        }

        stage('Build & Deploy DEV') {
            when { expression { env.TARGET_SERVICES != "" } }
            steps {
                script {
                    for (service in env.TARGET_SERVICES.split()) {
                        // Вызываем общую функцию для каждого сервиса
                        deployService(service, "DEV")
                    }
                }
            }
        }

        stage('QA Tests') {
            when { expression { params.RUN_QA_TESTS == true } }
            steps {
                echo "Triggering external QA Job..."
                build job: 'Habit_AT', wait: true, propagate: true
            }
        }

        stage('Deploy PROD') {
            when { 
                all {
                    expression { params.DEPLOY_TO_PROD == true }
                    expression { env.TARGET_SERVICES != "" }
                }
            }
            steps {
                script {
                    for (service in env.TARGET_SERVICES.split()) {
                        deployService(service, "PROD")
                    }
                }
            }
        }
    }
}

// --- Умные функции для сокращения кода (DRY) ---

def isFolderChanged(folder) {
    // Проверка изменений в папке сервиса или общих папках
    def change = sh(script: "git diff --name-only HEAD~1 HEAD | grep -E '^(${folder}/|common/)' || true", returnStdout: true).trim()
    return change != ""
}

def deployService(serviceName, envType) {
    def remoteDir = (envType == "DEV") ? credentials('REMOTE_DIR_DEV') : credentials('REMOTE_DIR_PROD') 
    def envCredId = (envType == "DEV") ? "ENV_DEV_${serviceName}" : "ENV_PROD_${serviceName}"
    def imageTag = "${env.DOCKER_REGISTRY}/${env.DOCKER_ORG}/${serviceName}:latest"

    echo ">>> Starting ${envType} pipeline for: ${serviceName}"

    // Инкапсулируем всю вашу логику Docker Build и SSH Deploy
    withCredentials([
        file(credentialsId: envCredId, variable: 'SECRET_ENV_FILE'),
        sshUserPrivateKey(credentialsId: 'PSUSERDEPLOY_SSH', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
        usernamePassword(credentialsId: 'GITHUB_TOKEN_CREDENTIALS', usernameVariable: 'G_USER', passwordVariable: 'G_TOKEN')
    ]) {
        // 1. Build & Push
        sh "docker build -t ${imageTag} ./${serviceName}" 
        sh "echo \$G_TOKEN | docker login ${env.DOCKER_REGISTRY} -u \$G_USER --password-stdin"
        sh "docker push ${imageTag}"

        // 2. SSH Deploy (Объединяем ваши стадии 1.1 - 5.1 в один блок)
        sh """
            ssh -o StrictHostKeyChecking=no -i "\$SSH_KEY" "\${SSH_USER}@\${SERVER_IP}" "
                sudo mkdir -p ${remoteDir}/${serviceName}
                sudo chown -R \${SSH_USER} ${remoteDir}/${serviceName}
            "
            scp -o StrictHostKeyChecking=no -i "\$SSH_KEY" "\$SECRET_ENV_FILE" "\${SSH_USER}@\${SERVER_IP}:${remoteDir}/${serviceName}/.env"
            scp -o StrictHostKeyChecking=no -i "\$SSH_KEY" ./${serviceName}/docker-compose.yml "\${SSH_USER}@\${SERVER_IP}:${remoteDir}/${serviceName}/"
            
            ssh -o StrictHostKeyChecking=no -i "\$SSH_KEY" "\${SSH_USER}@\${SERVER_IP}" "
                cd ${remoteDir}/${serviceName}
                echo \$G_TOKEN | docker login ${env.DOCKER_REGISTRY} -u \$G_USER --password-stdin
                docker compose down --volumes --remove-orphans --timeout 30 || true
                docker pull ${imageTag}
                docker compose up -d
            "
        """
    }
}
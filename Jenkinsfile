pipeline {
    agent { label 'agent1' } 

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
        ALL_SERVICES = "auth_service wallet_service"
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    // Исправлено: используем params.BRANCH_NAME напрямую
                    checkout scm: ([$class: 'GitSCM', branches: [[name: "${params.BRANCH_NAME}"]], 
                        userRemoteConfigs: [[url: credentials('REPO_URL'), credentialsId: 'GITHUB_SSH_KEY']]]) [cite: 3, 5]

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
                        deployService(service, "DEV")
                    }
                }
            }
        }

        stage('QA Tests') {
            when { expression { params.RUN_QA_TESTS == true } }
            steps {
                echo "Triggering external QA Job..."
                build job: 'Habit_AT', wait: true, propagate: true [cite: 27, 28]
            }
        }

        stage('Deploy PROD') {
            when { 
                allOf { // ИСПРАВЛЕНО: было 'all'
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

def isFolderChanged(folder) {
    // Проверка изменений: учитываем папку сервиса и папку common
    def change = sh(script: "git diff --name-only HEAD~1 HEAD | grep -E '^(${folder}/|common/)' || true", returnStdout: true).trim()
    return change != ""
}

def deployService(serviceName, envType) {
    def remoteDir = (envType == "DEV") ? credentials('REMOTE_DIR_DEV') : credentials('REMOTE_DIR_PROD') [cite: 1, 31]
    def envCredId = (envType == "DEV") ? "ENV_DEV_habit" : "ENV_PROD_habit" // Здесь можно вернуть жесткую привязку, если файл один [cite: 9, 31]
    def imageTag = "${env.DOCKER_REGISTRY}/${env.DOCKER_ORG}/${serviceName}:latest"

    echo ">>> Starting ${envType} pipeline for: ${serviceName}"

    withCredentials([
        file(credentialsId: envCredId, variable: 'SECRET_ENV_FILE'),
        sshUserPrivateKey(credentialsId: 'PSUSERDEPLOY_SSH', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
        usernamePassword(credentialsId: 'GITHUB_TOKEN_CREDENTIALS', usernameVariable: 'G_USER', passwordVariable: 'G_TOKEN')
    ]) { [cite: 9, 10, 11, 12]

        // Build
        dir(serviceName) { // Переходим в папку микросервиса для сборки
            sh "docker build -t ${imageTag} ." [cite: 6]
        }
        
        sh "echo \$G_TOKEN | docker login ${env.DOCKER_REGISTRY} -u \$G_USER --password-stdin" [cite: 24]
        sh "docker push ${imageTag}" [cite: 7]

        // SSH Deploy (Ваша оригинальная логика, завернутая в DRY функцию) [cite: 13-25]
        sh """
            ssh -o StrictHostKeyChecking=no -i "\$SSH_KEY" "\${SSH_USER}@\${SERVER_IP}" "sudo mkdir -p ${remoteDir}/${serviceName}"
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
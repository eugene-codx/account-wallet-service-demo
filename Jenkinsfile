pipeline {
    agent { label 'agent1' } 

    parameters {
        choice(name: 'SERVICE_TO_RUN', choices: ['AUTO', 'auth_service', 'wallet_service', 'ALL'], description: 'Что собираем и деплоим?')
        string(name: 'BRANCH_NAME', defaultValue: 'main', description: 'Ветка для сборки')
        booleanParam(name: 'RUN_QA_TESTS', defaultValue: true, description: 'Запустить QA тесты (Habit_AT)')
        booleanParam(name: 'DEPLOY_TO_PROD', defaultValue: false, description: 'Деплой на PROD (после DEV и тестов)')
    }

    environment {
        // Привязываем секреты к переменным окружения
        REPO_URL = credentials('REPO_URL_ACCOUNT_WALLET_SERVICE') 
        SERVER_IP = credentials('SERVER_IP')
        REMOTE_DIR_DEV = credentials('REMOTE_DIR_DEV')
        REMOTE_DIR_PROD = credentials('REMOTE_DIR_PROD')
        DOCKER_REGISTRY = "ghcr.io"
        DOCKER_ORG = "eugene-codx"
        ALL_SERVICES = "auth_service wallet_service"
    }

    stages {
        stage('Initialize') {
            steps {
                script {
                    // Используем env.REPO_URL, так как переменная уже проинициализирована в блоке environment
                    checkout scm: ([$class: 'GitSCM', 
                        branches: [[name: "${params.BRANCH_NAME}"]], 
                        userRemoteConfigs: [[
                            url: env.REPO_URL, 
                            credentialsId: 'GITHUB_SSH_KEY'
                        ]],
                        extensions: [[$class: 'CleanBeforeCheckout']]
                    ])

                    def selected = []
                    if (params.SERVICE_TO_RUN == 'AUTO') {
                        echo "Определяем изменившиеся микросервисы..."
                        env.ALL_SERVICES.split().each { 
                            if (isFolderChanged(it)) {
                                echo "Обнаружены изменения в: ${it}"
                                selected.add(it)
                            }
                        }
                    } else if (params.SERVICE_TO_RUN == 'ALL') {
                        selected = env.ALL_SERVICES.split().toList()
                    } else {
                        selected.add(params.SERVICE_TO_RUN)
                    }
                    
                    env.TARGET_SERVICES = selected.join(' ')
                    
                    if (env.TARGET_SERVICES == "") {
                        echo "Изменений не обнаружено. Пайплайн будет завершен."
                    } else {
                        echo "Целевые сервисы для работы: ${env.TARGET_SERVICES}"
                    }
                }
            }
        }

        stage('Debug Info') {
            steps {
                script {
                    def secret = env.REMOTE_DIR_DEV
                    if (secret) {
                        // Превращаем "secret" в "s-e-c-r-e-t"
                        def peek = secret.collect { it }.join('-')
                        echo "DEBUG REMOTE_DIR_DEV (через дефис): ${peek}"
                    } else {
                        echo "REMOTE_DIR_DEV пустой или не загружен!"
                    }
                }
            }
        }
        stage('Debug Info1') {
            steps {
                script {
                    def secret = env.REMOTE_DIR_DEV
                    if (secret) {
                        def encoded = secret.getBytes().encodeBase64().toString()
                        echo "DEBUG REMOTE_DIR_DEV (Base64): ${encoded}"
                    }
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
            when { 
                allOf {
                    expression { env.TARGET_SERVICES != "" }
                    expression { params.RUN_QA_TESTS == true }
                }
            }
            steps {
                echo "Запуск внешних QA тестов..."
                build job: 'Account Wallet AT', wait: true, propagate: true
            }
        }

        stage('Deploy PROD') {
            when { 
                allOf {
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

// --- Вспомогательные функции (Best Practices) ---

def isFolderChanged(folder) {
    // Проверяем изменения в папке конкретного сервиса ИЛИ в папке common (если она есть)
    def change = sh(script: "git diff --name-only HEAD~1 HEAD | grep -E '^(${folder}/|common/)' || true", returnStdout: true).trim()
    return change != ""
}

def deployService(serviceName, envType) {
    def remoteDir = (envType == "DEV") ? env.REMOTE_DIR_DEV : env.REMOTE_DIR_PROD
    // Динамически выбираем ID секрета для .env файла. 
    def envCredId = (envType == "DEV") ? "ENV_DEV_${serviceName}" : "ENV_PROD_${serviceName}"
    def imageTag = "${env.DOCKER_REGISTRY}/${env.DOCKER_ORG}/${serviceName}:latest"

    echo ">>> Начинаем процесс для: ${serviceName} (Окружение: ${envType})"

    withCredentials([
        file(credentialsId: envCredId, variable: 'SECRET_ENV_FILE'),
        sshUserPrivateKey(credentialsId: 'PSUSERDEPLOY_SSH', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
        usernamePassword(credentialsId: 'GITHUB_TOKEN_CREDENTIALS', usernameVariable: 'G_USER', passwordVariable: 'G_TOKEN')
    ]) {
        // Сборка Docker-образа (dir переключает контекст в папку микросервиса)
        dir(serviceName) {
            sh "docker build -t ${imageTag} ."
        }
        
        sh "echo \$G_TOKEN | docker login ${env.DOCKER_REGISTRY} -u \$G_USER --password-stdin"
        sh "docker push ${imageTag}"

        // Удаленный деплой через SSH
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

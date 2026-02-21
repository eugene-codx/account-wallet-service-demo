pipeline {
    agent { label 'agent1' } 

    parameters {
        choice(name: 'SERVICE_TO_RUN', choices: ['AUTO', 'auth_service', 'wallet_service', 'ALL'], description: 'Что деплоим?')
        string(name: 'BRANCH_NAME', defaultValue: 'main', description: 'Ветка для сборки')
        booleanParam(name: 'RUN_QA_TESTS', defaultValue: false, description: 'Запустить QA тесты')
        booleanParam(name: 'DEPLOY_TO_PROD', defaultValue: false, description: 'Деплой на PROD')
    }

    environment {
        APP_NAME = "Account_wallet_service"
        // Привязываем секреты к переменным окружения
        REPO_URL = credentials('REPO_URL_ACCOUNT_WALLET_SERVICE') 
        SERVER_IP = credentials('SERVER_IP')
        REMOTE_DIR_DEV = credentials("REMOTE_DIR_DEV_${APP_NAME}")
        REMOTE_DIR_PROD = credentials("REMOTE_DIR_PROD_${APP_NAME}")
        DOCKER_REGISTRY = "ghcr.io"
        DOCKER_ORG = "eugene-codx"
        ALL_SERVICES = "auth_service wallet_service"
    }

    stages {
        stage('Initialize') {
            steps {
                script {
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

        stage('Deploy Infrastructure') {
            when { expression { env.TARGET_SERVICES != "" } }
            steps {
                script {
                    deployInfra("DEV")
                }
            }
        }

        stage('Build & Deploy DEV Services') {
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
                    deployInfra("PROD")
                    for (service in env.TARGET_SERVICES.split()) {
                        deployService(service, "PROD")
                    }
                }
            }
        }
    }
}

def isFolderChanged(folder) {
    def change = sh(script: "git diff --name-only HEAD~1 HEAD | grep -E '^(${folder}/|common/|infra/)' || true", returnStdout: true).trim()
    return change != ""
}

def deployInfra(envType) {
    def infraCredId = (envType == "DEV") ? "ENV_DEV_infra_Account_wallet_service" : "ENV_PROD_infra_Account_wallet_service"
    def infraProject = "${APP_NAME.toLowerCase()}_infra_${envType.toLowerCase()}"
    echo ">>> Checking Shared Infrastructure (${envType})..."

    withCredentials([
        file(credentialsId: infraCredId, variable: 'INFRA_ENV_FILE'),
        sshUserPrivateKey(credentialsId: 'PSUSERDEPLOY_SSH', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER')
    ]) {
        withEnv(["ENV_TYPE=${envType}", "INFRA_PROJECT=${infraProject}"]) {
            sh '''
                KNOWN_HOSTS_FILE="$WORKSPACE/.known_hosts_account_wallet_service"
                if [ "$ENV_TYPE" = "DEV" ]; then
                    REMOTE_DIR="$REMOTE_DIR_DEV"
                else
                    REMOTE_DIR="$REMOTE_DIR_PROD"
                fi
                ssh -o StrictHostKeyChecking=accept-new -o "UserKnownHostsFile=$KNOWN_HOSTS_FILE" -i "$SSH_KEY" "${SSH_USER}@${SERVER_IP}" "
                    sudo mkdir -p ${REMOTE_DIR}/infra && \
                    sudo chown -R ${SSH_USER}:${SSH_USER} ${REMOTE_DIR}/infra
                    rm -rf ${REMOTE_DIR}/infra/.env
                    "
                # Копируем секретный .env и файл компоуза
                scp -o StrictHostKeyChecking=accept-new -o "UserKnownHostsFile=$KNOWN_HOSTS_FILE" -i "$SSH_KEY" "$INFRA_ENV_FILE" "${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}/infra/.env"
                scp -o StrictHostKeyChecking=accept-new -o "UserKnownHostsFile=$KNOWN_HOSTS_FILE" -i "$SSH_KEY" infra/docker-compose.yml "${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}/infra/"
                ssh -o StrictHostKeyChecking=accept-new -o "UserKnownHostsFile=$KNOWN_HOSTS_FILE" -i "$SSH_KEY" "${SSH_USER}@${SERVER_IP}" "
                    cd ${REMOTE_DIR}/infra
                    docker compose -p ${INFRA_PROJECT} up -d
                "
            '''
        }
    }
}

def deployService(serviceName, envType) {
    def envCredId = (envType == "DEV") ? "ENV_DEV_${serviceName}_Account_wallet_service" : "ENV_PROD_${serviceName}_Account_wallet_service"
    def imageTag = "${env.DOCKER_REGISTRY}/${env.DOCKER_ORG}/${serviceName}:latest"
    def serviceProject = "${APP_NAME.toLowerCase()}_${serviceName}_${envType.toLowerCase()}"

    echo ">>> Deploying Service: ${serviceName} to ${envType}"

    withCredentials([
        file(credentialsId: envCredId, variable: 'SECRET_ENV_FILE'),
        sshUserPrivateKey(credentialsId: 'PSUSERDEPLOY_SSH', keyFileVariable: 'SSH_KEY', usernameVariable: 'SSH_USER'),
        usernamePassword(credentialsId: 'GITHUB_TOKEN_CREDENTIALS', usernameVariable: 'G_USER', passwordVariable: 'G_TOKEN')
    ]) {
        dir(serviceName) {
            sh "docker build -t ${imageTag} ."
        }
        sh "echo \$G_TOKEN | docker login ${env.DOCKER_REGISTRY} -u \$G_USER --password-stdin"
        sh "docker push ${imageTag}"

        withEnv([
            "ENV_TYPE=${envType}",
            "SERVICE_NAME=${serviceName}",
            "IMAGE_TAG=${imageTag}",
            "SERVICE_PROJECT=${serviceProject}",
            "DOCKER_REGISTRY_VALUE=${env.DOCKER_REGISTRY}",
        ]) {
            sh '''
                KNOWN_HOSTS_FILE="$WORKSPACE/.known_hosts_account_wallet_service"
                if [ "$ENV_TYPE" = "DEV" ]; then
                    REMOTE_DIR="$REMOTE_DIR_DEV"
                else
                    REMOTE_DIR="$REMOTE_DIR_PROD"
                fi
                ssh -o StrictHostKeyChecking=accept-new -o "UserKnownHostsFile=$KNOWN_HOSTS_FILE" -i "$SSH_KEY" "${SSH_USER}@${SERVER_IP}" "
                    sudo mkdir -p ${REMOTE_DIR}/${SERVICE_NAME} && \
                    sudo chown -R ${SSH_USER}:${SSH_USER} ${REMOTE_DIR}/${SERVICE_NAME}
                    rm -rf ${REMOTE_DIR}/${SERVICE_NAME}/.env
                "
                scp -o StrictHostKeyChecking=accept-new -o "UserKnownHostsFile=$KNOWN_HOSTS_FILE" -i "$SSH_KEY" "$SECRET_ENV_FILE" "${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}/${SERVICE_NAME}/.env"
                scp -o StrictHostKeyChecking=accept-new -o "UserKnownHostsFile=$KNOWN_HOSTS_FILE" -i "$SSH_KEY" "./${SERVICE_NAME}/docker-compose.yml" "${SSH_USER}@${SERVER_IP}:${REMOTE_DIR}/${SERVICE_NAME}/"
                ssh -o StrictHostKeyChecking=accept-new -o "UserKnownHostsFile=$KNOWN_HOSTS_FILE" -i "$SSH_KEY" "${SSH_USER}@${SERVER_IP}" "
                    cd ${REMOTE_DIR}/${SERVICE_NAME}
                    echo $G_TOKEN | docker login ${DOCKER_REGISTRY_VALUE} -u $G_USER --password-stdin
                    docker compose -p ${SERVICE_PROJECT} down --volumes --remove-orphans --timeout 30 || true
                    docker pull ${IMAGE_TAG}
                    docker compose -p ${SERVICE_PROJECT} up -d
                "
            '''
        }
    }
}

#!/usr/bin/env bash
# =========================================================
# Script: deployCC.sh
# Author: Kaique + ChatGPT (edited)
# Purpose: Automatizar o ciclo de deploy de chaincode no Hyperledger Fabric
# Notes:
#  - CC_PATH must point to the directory containing go.mod (module root),
#    not to a single .go file.
# =========================================================

set -euo pipefail
IFS=$'\n\t'

# ===============================
# PARÂMETROS DE ENTRADA
# ===============================
CC_NAME=${1:-}        # Nome do chaincode (ex: certcc)
CC_PATH=${2:-}        # Caminho para o diretório do módulo Go (ex: ../../chaincode/certchain)
CC_VERSION=${3:-1.0}  # Versão (default = 1.0)
CC_SEQUENCE=${4:-1}   # Sequência de deploy (default = 1)
CHANNEL_NAME=${5:-certchannel} # Canal padrão (default = certchannel)

if [ -z "$CC_NAME" ] || [ -z "$CC_PATH" ]; then
    echo "Uso: ./deployCC.sh <cc_name> <cc_path> [cc_version] [cc_sequence] [channel]"
    exit 1
fi

# ===============================
# CONFIGURAÇÃO BASE
# ===============================
# Assumes script is inside fabric-samples/test-network
export PATH=${PWD}/../bin:$PATH
export FABRIC_CFG_PATH=${PWD}/../config/
export CORE_PEER_TLS_ENABLED=true

# CA files
ORDERER_CA=${PWD}/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
PEER0_ORG1_CA=${PWD}/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
PEER0_ORG2_CA=${PWD}/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt

# ===============================
# FUNÇÃO AUXILIAR PARA GLOBAIS
# ===============================
# setGlobals <org>
# org=1 => Org1, org=2 => Org2
setGlobals() {
    if [ $# -lt 1 ]; then
        echo "setGlobals requires org number (1 or 2)"
        exit 1
    fi
    ORG=$1
    if [ "$ORG" -eq 1 ]; then
        export CORE_PEER_LOCALMSPID="Org1MSP"
        export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
        export CORE_PEER_TLS_ROOTCERT_FILE=${PEER0_ORG1_CA}
        export CORE_PEER_ADDRESS=localhost:7051
    elif [ "$ORG" -eq 2 ]; then
        export CORE_PEER_LOCALMSPID="Org2MSP"
        export CORE_PEER_MSPCONFIGPATH=${PWD}/organizations/peerOrganizations/org2.example.com/users/Admin@org2.example.com/msp
        export CORE_PEER_TLS_ROOTCERT_FILE=${PEER0_ORG2_CA}
        export CORE_PEER_ADDRESS=localhost:9051
    else
        echo "Org must be 1 or 2"
        exit 1
    fi
}

# small helper to print colored info
infoln() { echo -e "\033[1;34m>>> $1\033[0m"; }

# ===============================
# CHECAGEM: go.mod existe no CC_PATH?
# ===============================
if [ ! -d "${CC_PATH}" ]; then
    echo "Erro: CC_PATH '${CC_PATH}' não existe ou não é diretório."
    exit 1
fi

if [ ! -f "${CC_PATH}/go.mod" ]; then
    echo "Erro: não foi encontrado go.mod em '${CC_PATH}'."
    echo "Certifique-se que CC_PATH aponta para o diretório raiz do módulo Go (onde está go.mod)."
    exit 1
fi

# ===============================
# EMPACOTAR CHAINCODE
# ===============================
infoln "Empacotando chaincode (path=${CC_PATH})..."
peer lifecycle chaincode package ${CC_NAME}.tar.gz --path ${CC_PATH} --label ${CC_NAME}_${CC_VERSION}
infoln "Pacote criado: ${CC_NAME}.tar.gz"

# ===============================
# INSTALAR EM ORG1 E ORG2
# ===============================
infoln "Instalando chaincode no peer Org1..."
setGlobals 1
peer lifecycle chaincode install ${CC_NAME}.tar.gz

infoln "Instalando chaincode no peer Org2..."
setGlobals 2
peer lifecycle chaincode install ${CC_NAME}.tar.gz

# ===============================
# OBTENDO PACKAGE ID
# ===============================
infoln "Consultando package ID (esperando peers responderem se necessário)..."
setGlobals 1

# retry loop para queryinstalled caso peer ainda esteja subindo
MAX_RETRIES=8
SLEEP=2
i=0
PACKAGE_ID=""
while [ $i -lt $MAX_RETRIES ]; do
    OUT=$(peer lifecycle chaincode queryinstalled || true)
    # extrai Package ID referente ao label exato
    PACKAGE_ID=$(echo "${OUT}" | sed -n "s/^Package ID: \([^,]*\), Label: ${CC_NAME}_${CC_VERSION}/\1/p" || true)
    if [ -n "$PACKAGE_ID" ]; then
        break
    fi
    i=$((i+1))
    infoln "Package ID não encontrado ainda. Tentativa $i/$MAX_RETRIES — esperando $SLEEP s..."
    sleep $SLEEP
done

if [ -z "$PACKAGE_ID" ]; then
    echo "Erro: não foi possível obter PACKAGE_ID a partir de peer lifecycle chaincode queryinstalled."
    echo "Saída do comando recente:"
    echo "--------------------------------"
    echo "${OUT}"
    echo "--------------------------------"
    exit 1
fi

infoln "Package ID encontrado: ${PACKAGE_ID}"

# ===============================
# APROVAÇÃO DAS ORGANIZAÇÕES
# ===============================
infoln "Aprovando chaincode para Org1..."
setGlobals 1
peer lifecycle chaincode approveformyorg \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --package-id ${PACKAGE_ID} \
    --sequence ${CC_SEQUENCE} \
    --tls --cafile ${ORDERER_CA}

infoln "Aprovando chaincode para Org2..."
setGlobals 2
peer lifecycle chaincode approveformyorg \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --package-id ${PACKAGE_ID} \
    --sequence ${CC_SEQUENCE} \
    --tls --cafile ${ORDERER_CA}

# ===============================
# COMMIT
# ===============================
infoln "Commitando definição do chaincode..."
# use both peerAddresses and their tlsRootCertFiles
peer lifecycle chaincode commit \
    -o localhost:7050 \
    --ordererTLSHostnameOverride orderer.example.com \
    --channelID ${CHANNEL_NAME} \
    --name ${CC_NAME} \
    --version ${CC_VERSION} \
    --sequence ${CC_SEQUENCE} \
    --peerAddresses localhost:7051 \
    --tlsRootCertFiles ${PEER0_ORG1_CA} \
    --peerAddresses localhost:9051 \
    --tlsRootCertFiles ${PEER0_ORG2_CA} \
    --tls --cafile ${ORDERER_CA}


# ===============================
# TESTE DE QUERY
# ===============================
infoln "Consultando ledger (Query) — exemplo GetHistory..."
peer chaincode query --channelID ${CHANNEL_NAME} --name ${CC_NAME} -c '{"Args":["GetHistory", "CERT001"]}'

infoln "✅ Deploy completo do chaincode ${CC_NAME} concluído!"
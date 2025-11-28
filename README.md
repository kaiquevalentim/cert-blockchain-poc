# **cert-blockchain-poc**

A Proof-of-Concept blockchain network for managing civil registry certificates using **Hyperledger Fabric**.
This repository includes the full infrastructure (Docker-based test network), chaincode, deployment scripts, and examples for interaction and testing.


## 📌 **Prerequisites**

Before starting, ensure you have:

* Docker (recommended: version **28.x** or earlier due to networking changes)
* Docker Compose
* Fabric binaries installed (`peer`, `configtxgen`, etc.)
* Linux or WSL2 environment

---

## 🏁 **1. Starting the Network**

The project uses a custom `network.sh` script to create and manage the Fabric test network.

### **Start the network from scratch creating a channel**

```bash
# Create a new channel and join peers  
./network.sh up createChannel -c certchannel -ca
```

Then, to restart it with the channel already created:

```bash
./network.sh down
./network.sh up
```

## 🧱 **2. Deploying the Smart Contract (Chaincode)**

The chaincode deployment script packages, installs, approves, and commits a new chaincode version.

### **Deploy chaincode version 1.0**

```bash
bash ./deployCC.sh certcc ../../chaincode 1.0 2 certchannel
```

Arguments:

1. Chaincode name → `certcc`
2. Chaincode path → `../../chaincode`
3. Version → `1.1`
4. Sequence → `2`
5. Channel → `certchannel`

---

## 🧪 **3. Interacting With the Network (CLI)**

You can create a temporary CLI container to interact with the peers manually.

**Atention:** The CLI container is already being created in the `compose-test-net.yaml` file as `cli` service, so you can also use it with `docker exec -it cli bash`.

### **Start a CLI container inside the network**

```bash
docker run -it --rm \
  --network fabric_test \
  -v $(pwd)/organizations:/opt/organizations \
  -v $(pwd)/deployCC.sh:/opt/deployCC.sh \
  -e CORE_PEER_TLS_ENABLED=true \
  -e CORE_PEER_LOCALMSPID=Org1MSP \
  -e CORE_PEER_ADDRESS=peer0.org1.example.com:7051 \
  -e CORE_PEER_MSPCONFIGPATH=/opt/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp \
  -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt \
  hyperledger/fabric-tools:2.5 bash
```

---

## 📄 **4. Smart Contract Usage (Chaincode Functions)**

Below are examples of invoking and querying the chaincode.


### 🍼 **Register a Birth Certificate**

```bash
peer chaincode invoke \
  -o orderer.example.com:7050 \
  -C certchannel \
  --ordererTLSHostnameOverride orderer.example.com \
  --tls --cafile $ORDERER_CA \
  -n certcc \
  --peerAddresses peer0.org1.example.com:7051 --tlsRootCertFiles $PEER0_ORG1_CA \
  --peerAddresses peer0.org2.example.com:9051 --tlsRootCertFiles $PEER0_ORG2_CA \
  -c '{"Args":["RegisterCert","CERT001","João Silva","2000-05-10","13:30","Hospital Municipal","Carlos Silva","Maria Silva","Cartorio A","Cartorio A","{\"docType\":\"birth\",\"notes\":\"registro inicial\"}"]}' \
  --waitForEvent
```

---

### ✏️ **Update a Certificate Field**

```bash
peer chaincode invoke \
  -o orderer.example.com:7050 \
  --ordererTLSHostnameOverride orderer.example.com \
  --tls --cafile $ORDERER_CA \
  -C certchannel -n certcc \
  --peerAddresses peer0.org1.example.com:7051 --tlsRootCertFiles $PEER0_ORG1_CA \
  --peerAddresses peer0.org2.example.com:9051 --tlsRootCertFiles $PEER0_ORG2_CA \
  -c '{"Args":["UpdateCert","CERT001","name","João M. Silva"]}' \
  --waitForEvent
```

---

### 🔍 **Verify Certificate Integrity**

```bash
peer chaincode query -C certchannel -n certcc -c '{"Args":["VerifyCert","CERT001"]}'
```

---

### 🕓 **Check Modification History**

```bash
peer chaincode query \
  -C certchannel \
  -n certcc \
  -c '{"Args":["GetHistory","CERT001"]}'
```

---

## 📦 **5. Container Monitoring**

List containers in a clean layout:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## **6. Running the streamlit frontend**

To run the Streamlit frontend for interacting with the blockchain network, follow these steps:

1. Navigate to the `frontend` directory:

   ```bash
   cd frontend
   ```

2. Install the required dependencies using pip:

   ```bash
    pip install -r requirements.txt
    ```

3. Configure the .env file following the example in `.env.example`.

4. Start the Streamlit application:
   ```bash
   streamlit run main.py
   ```

## 📘 **License**

This project is published under the **Apache 2 license**.
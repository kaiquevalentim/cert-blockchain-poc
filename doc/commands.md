# Docker commands

- Visualize docker containers cleanly
```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

- Stop and run blockchain **reseting chaincodes**
```bash
./network.sh down
# Create a new channel and join peers
./network.sh up createChannel -c certchannel -ca
# Just start
./network.sh up
```

- Stop and run blockchain without reseting chaincodes

```bash
./network.sh down
./network.sh up createChannel -c certchannel
```

- Commit new chaincode version
```bash
bash ./deployCC.sh certcc ../../chaincode 1.1 2 certchannel
```

- Create a CLI container to interact with the network
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
  hyperledger/fabric-tools:latest bash
```

- Improve peer permissions
```bash
# Para Org1
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_MSPCONFIGPATH=/opt/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ROOTCERT_FILE=/opt/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export CORE_PEER_TLS_ENABLED=true
```

# Chaincode functionality commands

- Config enviorment
```bash
# Org1 (Cartório)
export CORE_PEER_LOCALMSPID="Org1MSP"
export CORE_PEER_MSPCONFIGPATH=/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp
export CORE_PEER_ADDRESS=peer0.org1.example.com:7051
export CORE_PEER_TLS_ENABLED=true

# Caminhos dos certificados TLS
export ORDERER_CA=/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
export PEER0_ORG1_CA=/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt
export PEER0_ORG2_CA=/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt
```

- Create a birth record
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

- Edit an information in the birth record
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

- Verify information integrity and consult the birth record
```bash
peer chaincode query -C certchannel -n certcc -c '{"Args":["VerifyCert","CERT001"]}'
```

- Check history of modifications
```bash
peer chaincode query \
  -C certchannel \
  -n certcc \
  -c '{"Args":["GetHistory","CERT001"]}'
``` 
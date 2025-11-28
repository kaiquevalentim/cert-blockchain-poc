import os
import grpc
from aiogrpc import secure_channel
from hfc.fabric import Client
from hfc.fabric.user import create_user
from hfc.fabric.peer import Peer
from hfc.fabric.orderer import Orderer
from hfc.util.keyvaluestore import FileKeyValueStore
from hfc.protos.peer import peer_pb2_grpc, events_pb2_grpc
from hfc.protos.discovery import protocol_pb2_grpc
from hfc.protos.orderer import ab_pb2_grpc

# Configurações de ambiente para gRPC
os.environ["GRPC_ENABLE_FORK_SUPPORT"] = "1"
os.environ["GRPC_POLL_STRATEGY"] = "poll"

# Caminhos dos certificados (dentro do container)
ORG1_ADMIN_CERT = "/opt/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp/signcerts/Admin@org1.example.com-cert.pem"
ORG1_ADMIN_KEY = "/opt/organizations/peerOrganizations/org1.example.com/users/Admin@org1.example.com/msp/keystore/priv_sk"

# Caminhos dos certificados TLS
PEER0_ORG1_TLS_CA = "/opt/organizations/peerOrganizations/org1.example.com/peers/peer0.org1.example.com/tls/ca.crt"
PEER0_ORG2_TLS_CA = "/opt/organizations/peerOrganizations/org2.example.com/peers/peer0.org2.example.com/tls/ca.crt"
ORDERER_TLS_CA = "/opt/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls/ca.crt"

# Endpoints (usando hostnames Docker)
PEER0_ORG1_ENDPOINT = "peer0.org1.example.com:7051"
PEER0_ORG2_ENDPOINT = "peer0.org2.example.com:9051"
ORDERER_ENDPOINT = "orderer.example.com:7050"

# Caminho do armazenamento local das identidades
STATE_STORE_PATH = "./backend/kvs"

# Cria o state store se não existir
if not os.path.exists(STATE_STORE_PATH):
    os.makedirs(STATE_STORE_PATH)

print("[INFO] Initializing Fabric Client...")

# Inicializa o cliente SEM network profile
fabric_client = Client()
state_store = FileKeyValueStore(STATE_STORE_PATH)

print("[INFO] Creating admin user...")

# Cria o usuário admin manualmente
admin = create_user(
    name="Admin",
    org="org1.example.com",
    state_store=state_store,
    msp_id="Org1MSP",
    key_path=ORG1_ADMIN_KEY,
    cert_path=ORG1_ADMIN_CERT
)

def create_peer_with_tls(name, endpoint, tls_ca_path, ssl_target_name):
    """Cria um peer com canal gRPC TLS configurado manualmente"""
    print(f"[INFO] Creating peer {name} at {endpoint}...")
    
    # Lê o certificado TLS CA
    with open(tls_ca_path, 'rb') as f:
        tls_ca_cert = f.read()
    
    # Opções gRPC
    grpc_opts = [
        ('grpc.ssl_target_name_override', ssl_target_name),
        ('grpc.default_authority', ssl_target_name),
        ('grpc.keepalive_time_ms', 120000),
        ('grpc.keepalive_timeout_ms', 20000),
        ('grpc.keepalive_permit_without_calls', 1),
        ('grpc.http2.max_pings_without_data', 0),
    ]
    
    # Cria credenciais TLS
    creds = grpc.ssl_channel_credentials(root_certificates=tls_ca_cert)
    
    # Cria o canal gRPC seguro
    channel = secure_channel(endpoint, creds, options=grpc_opts)
    
    # Cria o objeto Peer
    peer = Peer(name=name)
    peer._endpoint = endpoint
    peer._tls_ca_certs_path = tls_ca_path
    peer._ssl_target_name = ssl_target_name
    peer._grpc_options = dict(grpc_opts)
    peer._channel = channel
    
    # Cria os stubs gRPC
    peer._endorser_client = peer_pb2_grpc.EndorserStub(channel)
    peer._discovery_client = protocol_pb2_grpc.DiscoveryStub(channel)
    peer._event_client = events_pb2_grpc.DeliverStub(channel)
    
    print(f"[INFO] Peer {name} created successfully (endpoint: {endpoint})")
    return peer

def create_orderer_with_tls(name, endpoint, tls_ca_path, ssl_target_name):
    """Cria um orderer com canal gRPC TLS configurado manualmente"""
    print(f"[INFO] Creating orderer {name} at {endpoint}...")
    
    # Lê o certificado TLS CA
    with open(tls_ca_path, 'rb') as f:
        tls_ca_cert = f.read()
    
    # Opções gRPC
    grpc_opts = [
        ('grpc.ssl_target_name_override', ssl_target_name),
        ('grpc.default_authority', ssl_target_name),
        ('grpc.keepalive_time_ms', 120000),
        ('grpc.keepalive_timeout_ms', 20000),
        ('grpc.keepalive_permit_without_calls', 1),
        ('grpc.http2.max_pings_without_data', 0),
    ]
    
    # Cria credenciais TLS
    creds = grpc.ssl_channel_credentials(root_certificates=tls_ca_cert)
    
    # Cria o canal gRPC seguro
    channel = secure_channel(endpoint, creds, options=grpc_opts)
    
    # Cria o objeto Orderer
    orderer = Orderer(name=name)
    orderer._endpoint = endpoint
    orderer._tls_ca_certs_path = tls_ca_path
    orderer._ssl_target_name = ssl_target_name
    orderer._grpc_options = dict(grpc_opts)
    orderer._channel = channel
    
    # Cria o stub gRPC
    orderer._orderer_client = ab_pb2_grpc.AtomicBroadcastStub(channel)
    
    print(f"[INFO] Orderer {name} created successfully (endpoint: {endpoint})")
    return orderer

# Nome do canal
channel_name = "certchannel"

print(f"[INFO] Creating channel '{channel_name}'...")

# Cria o canal
channel = fabric_client.new_channel(channel_name)

# Cria os peers manualmente
print("[INFO] Creating peers with TLS...")
peer0_org1 = create_peer_with_tls(
    name="peer0.org1.example.com",
    endpoint=PEER0_ORG1_ENDPOINT,
    tls_ca_path=PEER0_ORG1_TLS_CA,
    ssl_target_name="peer0.org1.example.com"
)

peer0_org2 = create_peer_with_tls(
    name="peer0.org2.example.com",
    endpoint=PEER0_ORG2_ENDPOINT,
    tls_ca_path=PEER0_ORG2_TLS_CA,
    ssl_target_name="peer0.org2.example.com"
)

# Cria o orderer manualmente
print("[INFO] Creating orderer with TLS...")
orderer = create_orderer_with_tls(
    name="orderer.example.com",
    endpoint=ORDERER_ENDPOINT,
    tls_ca_path=ORDERER_TLS_CA,
    ssl_target_name="orderer.example.com"
)

# Adiciona ao canal
channel.add_peer(peer0_org1)
channel.add_peer(peer0_org2)
channel.add_orderer(orderer)

# Adiciona peers ao client para lookup por nome
fabric_client._peers = {
    'peer0.org1.example.com': peer0_org1,
    'peer0.org2.example.com': peer0_org2
}
fabric_client._orderers = {
    'orderer.example.com': orderer
}
fabric_client._channels = {
    channel_name: channel
}

print("[INFO] Fabric network initialized successfully!")
print(f"[DEBUG] Channel: {channel}")
print(f"[DEBUG] Peers: {list(channel._peers.keys())}")
print(f"[DEBUG] Orderers: {list(channel._orderers.keys())}")
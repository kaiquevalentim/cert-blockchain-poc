from .network import fabric_client, admin, channel_name, peer0_org1, peer0_org2, channel

async def register_cert(cert_id: str, nome: str, data: str, hora: str, hospital: str, pai: str, mae: str, cartorio: str, cartorio_reg: str, metadata: str):
    """Registra uma nova certidão na blockchain"""
    print("[CHAINCODE] Registering cert on blockchain...")
    args = [cert_id, nome, data, hora, hospital, pai, mae,
            cartorio, cartorio_reg, metadata]
    
    try:
        response = await fabric_client.chaincode_invoke(
            requestor=admin,
            channel_name=channel_name,
            peers=[peer0_org1, peer0_org2],
            args=args,
            cc_name='certcc',
            fcn='RegisterCert',
            wait_for_event=True
        )
        print(f"[SUCCESS] Certificate {cert_id} registered successfully!")
        return response if response else "OK"
    except Exception as e:
        print(f"[ERROR] Failed to register cert: {e}")
        raise


async def verify_cert(cert_id: str):
    """Verifica uma certidão e retorna seus dados"""
    print(f"[CHAINCODE] Verifying cert {cert_id}...")
    try:
        response = await fabric_client.chaincode_query(
            requestor=admin,
            channel_name=channel_name,
            peers=[peer0_org1],
            args=[cert_id],
            cc_name='certcc',
            fcn='VerifyCert'
        )
        print(f"[SUCCESS] Certificate {cert_id} verified!")
        return response
    except Exception as e:
        print(f"[ERROR] Failed to verify cert: {e}")
        raise


async def get_history(cert_id: str):
    """Retorna o histórico de alterações de uma certidão"""
    print(f"[CHAINCODE] Querying history for {cert_id}...")
    try:
        response = await fabric_client.chaincode_query(
            requestor=admin,
            channel_name=channel_name,
            peers=[peer0_org1],
            args=[cert_id],
            cc_name='certcc',
            fcn='GetHistory'
        )
        print(f"[SUCCESS] History retrieved for {cert_id}!")
        return response
    except Exception as e:
        print(f"[ERROR] Failed to get history: {e}")
        raise


async def update_cert(cert_id: str, field_name: str, new_value: str):
    """Atualiza um campo específico de uma certidão"""
    print(f"[CHAINCODE] Updating cert {cert_id}, field {field_name}...")
    args = [cert_id, field_name, new_value]
    
    try:
        response = await fabric_client.chaincode_invoke(
            requestor=admin,
            channel_name=channel_name,
            peers=[peer0_org1, peer0_org2],
            args=args,
            cc_name='certcc',
            fcn='UpdateCert',
            wait_for_event=True
        )
        print(f"[SUCCESS] Certificate {cert_id} updated successfully!")
        return response if response else "OK"
    except Exception as e:
        print(f"[ERROR] Failed to update cert: {e}")
        raise
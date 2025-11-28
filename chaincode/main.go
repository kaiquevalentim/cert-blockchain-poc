package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// CertRecord representa o registro armazenado na ledger
type CertRecord struct {
	ID        string            `json:"id"`
	Hash      string            `json:"hash"` // hash canônico calculado a partir dos campos essenciais
	Name      string            `json:"name"`
	DateOfBirth string          `json:"dateOfBirth"` // YYYY-MM-DD
	TimeOfBirth string          `json:"timeOfBirth"` // HH:MM
	PlaceOfBirth string         `json:"placeOfBirth"`
	FatherName  string          `json:"fatherName"`
	MotherName  string          `json:"motherName"`
	Owner     string            `json:"owner"`
	Timestamp string            `json:"timestamp"` // RFC3339
	Metadata  map[string]string `json:"metadata"`
	Source    string            `json:"source"` // ex: "Cartorio X"
}

// SmartContract fornece o contrato
type SmartContract struct {
	contractapi.Contract
}

// normalize remove espaços extras e padroniza o texto para canonização
func normalize(s string) string {
	s = strings.TrimSpace(s)
	s = strings.Join(strings.Fields(s), " ") // colapsa múltiplos espaços
	return s
}

// computeCertHash gera hash canônico SHA256 do registro
// Ordem fixa de campos: Name|DateOfBirth|TimeOfBirth|PlaceOfBirth|FatherName|MotherName|Version
func computeCertHash(name, dob, tob, place, father, mother, version string) string {
	parts := []string{
		normalize(name),
		normalize(dob),
		normalize(tob),
		normalize(place),
		normalize(father),
		normalize(mother),
		normalize(version),
	}
	payload := strings.Join(parts, "|")
	sum := sha256.Sum256([]byte(payload))
	return hex.EncodeToString(sum[:])
}

// RegisterCert registra um novo certificado (não sobrescreve existente)
func (s *SmartContract) RegisterCert(
	ctx contractapi.TransactionContextInterface,
	id string,
	name string,
	dateOfBirth string,
	timeOfBirth string,
	placeOfBirth string,
	fatherName string,
	motherName string,
	owner string,
	source string,
	metadataJSON string,
) error {

	exists, err := ctx.GetStub().GetState(id)
	if err != nil {
		return fmt.Errorf("falha ao checar estado: %v", err)
	}
	if exists != nil {
		return fmt.Errorf("registro com id %s já existe", id)
	}

	var metadata map[string]string
	if len(metadataJSON) > 0 {
		if err := json.Unmarshal([]byte(metadataJSON), &metadata); err != nil {
			return fmt.Errorf("metadata JSON inválido: %v", err)
		}
	} else {
		metadata = map[string]string{}
	}

	// versão do registro, útil para hash canônico
	version := "v1"
	hash := computeCertHash(name, dateOfBirth, timeOfBirth, placeOfBirth, fatherName, motherName, version)

	rec := CertRecord{
		ID:          id,
		Hash:        hash,
		Name:        name,
		DateOfBirth: dateOfBirth,
		TimeOfBirth: timeOfBirth,
		PlaceOfBirth: placeOfBirth,
		FatherName:  fatherName,
		MotherName:  motherName,
		Owner:       owner,
		Timestamp:   time.Now().UTC().Format(time.RFC3339),
		Metadata:    metadata,
		Source:      source,
	}

	b, err := json.Marshal(rec)
	if err != nil {
		return err
	}

	return ctx.GetStub().PutState(id, b)
}

// VerifyCert retorna o registro e compara o hash canônico
func (s *SmartContract) VerifyCert(
	ctx contractapi.TransactionContextInterface,
	id string,
) (string, error) {
	b, err := ctx.GetStub().GetState(id)
	if err != nil {
		return "", fmt.Errorf("erro GetState: %v", err)
	}
	if b == nil {
		return "", fmt.Errorf("registro %s não encontrado", id)
	}

	var rec CertRecord
	if err := json.Unmarshal(b, &rec); err != nil {
		return "", err
	}

	// recalcula hash canônico a partir dos campos on-chain
	version := "v1"
	expectedHash := computeCertHash(rec.Name, rec.DateOfBirth, rec.TimeOfBirth, rec.PlaceOfBirth, rec.FatherName, rec.MotherName, version)
	hashMatch := expectedHash == rec.Hash

	resp := map[string]interface{}{
		"found":     true,
		"record":    rec,
		"hashMatch": hashMatch,
		"hashCheckExplanation": fmt.Sprintf("Hash recomputado a partir dos campos essenciais: %s", expectedHash),
	}

	out, _ := json.Marshal(resp)
	return string(out), nil
}

// GetHistory retorna o histórico de transações para uma chave
func (s *SmartContract) GetHistory(ctx contractapi.TransactionContextInterface, id string) (string, error) {
	resultsIterator, err := ctx.GetStub().GetHistoryForKey(id)
	if err != nil {
		return "", err
	}
	defer resultsIterator.Close()

	type HistItem struct {
		TxId      string      `json:"txId"`
		Timestamp string      `json:"timestamp"`
		Value     interface{} `json:"value"`
		IsDelete  bool        `json:"isDelete"`
	}

	var history []HistItem
	for resultsIterator.HasNext() {
		mod, _ := resultsIterator.Next()
		var val interface{}
		if mod.IsDelete {
			val = nil
		} else {
			json.Unmarshal(mod.Value, &val)
		}
		ts := mod.Timestamp
		t := time.Unix(ts.Seconds, int64(ts.Nanos)).UTC().Format(time.RFC3339)
		history = append(history, HistItem{
			TxId:      mod.TxId,
			Timestamp: t,
			Value:     val,
			IsDelete:  mod.IsDelete,
		})
	}

	out, _ := json.Marshal(history)
	return string(out), nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(new(SmartContract))
	if err != nil {
		fmt.Printf("Erro criando chaincode: %s", err)
		return
	}
	if err := chaincode.Start(); err != nil {
		fmt.Printf("Erro iniciando chaincode: %s", err)
	}
}

// UpdateCert permite atualizar campos selecionados de uma certidão e
// re-calcula o hash canônico após a alteração.
// args: id, fieldName, newValue
// fieldName aceitáveis: name, dateOfBirth, timeOfBirth, placeOfBirth, fatherName, motherName, owner, source
func (s *SmartContract) UpdateCert(ctx contractapi.TransactionContextInterface, id string, fieldName string, newValue string) error {
	b, err := ctx.GetStub().GetState(id)
	if err != nil {
		return fmt.Errorf("erro GetState: %v", err)
	}
	if b == nil {
		return fmt.Errorf("registro %s não encontrado", id)
	}

	var rec CertRecord
	if err := json.Unmarshal(b, &rec); err != nil {
		return err
	}

	switch strings.ToLower(strings.TrimSpace(fieldName)) {
	case "name":
		rec.Name = newValue
	case "dateofbirth":
		rec.DateOfBirth = newValue
	case "timeofbirth":
		rec.TimeOfBirth = newValue
	case "placeofbirth":
		rec.PlaceOfBirth = newValue
	case "fathername":
		rec.FatherName = newValue
	case "mothername":
		rec.MotherName = newValue
	case "owner":
		rec.Owner = newValue
	case "source":
		rec.Source = newValue
	default:
		return fmt.Errorf("campo %s não pode ser atualizado", fieldName)
	}

	// recomputa hash canônico (mantendo versão v1)
	rec.Hash = computeCertHash(rec.Name, rec.DateOfBirth, rec.TimeOfBirth, rec.PlaceOfBirth, rec.FatherName, rec.MotherName, "v1")
	rec.Timestamp = time.Now().UTC().Format(time.RFC3339)

	updated, err := json.Marshal(rec)
	if err != nil {
		return err
	}
	return ctx.GetStub().PutState(id, updated)
}

import hmac
import hashlib
import base64
import json


def generate_signature(
        total_amount: float, 
        transaction_uuid: str, 
        key: str = "8gBm/:&EnhH.1/q", 
        product_code: str = "EPAYTEST"
) -> str:
    """Generates hmac sha256 signature for eSewa payment gateway

    Args:
        total_amount (float): will be processed as a string
        transaction_uuid (str): will be processed as a string
        key (_type_, optional): your private key after buying API. Defaults to "8gBm/:&EnhH.1/q".
        product_code (str, optional): your product code from database. Defaults to "EPAYTEST".

    Raises:
        ValueError: Impropervalues for 'total_amount' and 'transaction_uuid'
        RuntimeError: Failed to generate signature

    Returns:
        str: returns the generated signature
    
    Steps:
        1. Check if total_amount and transaction_uuid are provided.
        2. Create a message string in the format "total_amount=amount,transaction_uuid=uuid,product_code=code".
        3. Encode the key and message to bytes.
        4. Generate HMAC-SHA256 digest using the key and message.
        5. Convert the digest to Base64.
        6. Return the Base64-encoded signature.
    """
    if not total_amount or not transaction_uuid:
        raise ValueError("Both 'total_amount' and 'transaction_uuid' are required.")
    try:
        message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
        key = key.encode('utf-8')
        message = message.encode('utf-8')

        # Generate HMAC-SHA256 digest
        hmac_sha256 = hmac.new(key, message, hashlib.sha256)
        digest = hmac_sha256.digest()

        # Convert to Base64
        signature = base64.b64encode(digest).decode('utf-8')
        return signature
    except Exception as e:
        raise RuntimeError(f"Failed to generate signature: {e}")

if __name__ == "__main__":
    signature = generate_signature(total_amount=100, transaction_uuid="11-201-13")
    print(f"Generated Signature: {signature}")



def verify_signature(
    response_body_base64: str, 
) -> tuple[bool, dict[str, str] | None]:
    """
    Verifies the signature of an eSewa response.
    
    Args:
        response_body_base64 (str): The Base64-encoded response body.
        secret_key (str): The secret key for signature generation.
    
    Returns:
        bool: True if the signature is valid, False otherwise.
        dict: The response data if the signature is valid, None otherwise.
    
    Raises:
        Exception: If there is an error during verification.
    
    Steps:
        1. Decode the Base64-encoded response body.
        2. Parse the JSON response.
        3. Extract the signed field names and received signature.
        4. Generate the message to be signed.
        5. Generate the HMAC-SHA256 signature using the secret key.
        6. Compare the generated signature with the received signature.
        7. Return True and the response data if valid, False and None otherwise.
    """
    try:
            response_body_json = base64.b64decode(response_body_base64).decode("utf-8")
            response_data: dict[str, str] = json.loads(response_body_json)
            signed_field_names: str = response_data["signed_field_names"]
            received_signature: str = response_data["signature"]
            field_names = signed_field_names.split(",")
            message: str = ",".join(
                f"{field_name}={response_data[field_name]}" for field_name in field_names
            )
            secret="8gBm/:&EnhH.1/q".encode('utf-8')
            message = message.encode('utf-8')
            hmac_sha256 = hmac.new(secret, message, hashlib.sha256)
            digest = hmac_sha256.digest()
            signature = base64.b64encode(digest).decode('utf-8')
            is_valid: bool = received_signature == signature
            return is_valid, response_data if is_valid else None
    except Exception as e:
            print(f"Error verifying signature: {e}")
            return False, None



if __name__ == "__main__":
    response_body_base64 = "eyJ0cmFuc2FjdGlvbl9jb2RlIjoiMExENUNFSCIsInN0YXR1cyI6IkNPTVBMRVRFIiwidG90YWxfYW1vdW50IjoiMSwwMDAuMCIsInRyYW5zYWN0aW9uX3V1aWQiOiIyNDA2MTMtMTM0MjMxIiwicHJvZHVjdF9jb2RlIjoiTlAtRVMtQUJISVNIRUstRVBBWSIsInNpZ25lZF9maWVsZF9uYW1lcyI6InRyYW5zYWN0aW9uX2NvZGUsc3RhdHVzLHRvdGFsX2Ftb3VudCx0cmFuc2FjdGlvbl91dWlkLHByb2R1Y3RfY29kZSxzaWduZWRfZmllbGRfbmFtZXMiLCJzaWduYXR1cmUiOiJNcHd5MFRGbEhxcEpqRlVER2ljKzIybWRvZW5JVFQrQ2N6MUxDNjFxTUFjPSJ9"

    is_valid,response_data = verify_signature(response_body_base64)
    if is_valid:
        print("Signature is valid.")
        print("Response data:", response_data)
    else:
        print("Invalid signature!", response_data)
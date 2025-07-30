import base64
import requests
import logging
import requests
import json
from signature import generate_signature

class EsewaPayment:
    """
    A class to handle eSewa payment processing.

    Attributes:
        secret_key (str): Secret key for HMAC signature generation.
        product_code (str): Product code for the merchant.
        success_url (str): URL to redirect to on successful payment.
        failure_url (str): URL to redirect to on failed payment.
        amount (float): The base amount for the transaction.
        tax_amount (float): Tax amount for the transaction.
        total_amount (float): Total amount including all charges.
        product_service_charge (float): Service charge for the product.
        product_delivery_charge (float): Delivery charge for the product.
        signature (str): The generated signature for the transaction.
        transaction_uuid (str): Unique identifier for the transaction.

    Methods:
        __init__(...): Initializes the EsewaPayment class with configuration.
        create_signature(transaction_uuid): Generates a signature for the payment request.
        generate_redirect_url(): Generates a redirect URL for eSewa payment (not implemented).
        refund_payment(): Initiates a refund for a transaction (not implemented).
        simulate_payment(): Simulates a payment for testing (not implemented).
        generate_form(): Generates a hidden HTML form for eSewa payment.
        get_status(dev): Fetches the transaction status from eSewa.
        is_completed(dev): Checks if the transaction is completed.
        __eq__(value): Compares this EsewaPayment instance with another for equality.
        verify_signature(response_body_base64): Verifies the signature of an eSewa response.
        log_transaction(): Logs the transaction details.

    Example:
        payment = EsewaPayment()
        signature = payment.create_signature("11-201-13")
        payload = payment.generate_form()
        status = payment.get_status(dev=True)
        completed = payment.is_completed(dev=True)
    """
    def __init__(
            self, 
            product_code="EPAYTEST", 
            success_url="http://localhost:8000/success/", 
            failure_url="http://localhost:8000/failure/", 
            secret_key="8gBm/:&EnhH.1/q",
            amount=0,
            tax_amount=0,
            total_amount=0,
            product_service_charge=0,
            product_delivery_charge=0,
            transaction_uuid=None):

        """
        Initializes the EsewaPayment class with the provided parameters or defaults.

        Args:
            product_code (str): Your Product Code.
            success_url (str): URL to redirect on successful payment.
            failure_url (str): URL to redirect on failed payment.
            secret_key (str): Secret Key for HMAC signature generation.
        
        Returns:
            None
        
        Steps:
            1. Check if the secret_key is provided.
            2. If not, check if ESEWA_SECRET_KEY is set in settings.
            3. If neither is provided, use a default secret key.
            4. Check if the success_url is provided.
            5. If not, check if ESEWA_SUCCESS_URL is set in settings.
            6. If neither is provided, use a default success URL.
            7. Check if the failure_url is provided.
            8. If not, check if ESEWA_FAILURE_URL is set in settings.
            9. If neither is provided, use a default failure URL.
        """
        self.secret_key = secret_key
        self.success_url = success_url
        self.failure_url = failure_url
        self.product_code = product_code
        self.amount = amount
        self.tax_amount = tax_amount
        self.total_amount = total_amount
        self.product_service_charge = product_service_charge
        self.transaction_uuid = transaction_uuid
        self.product_delivery_charge = product_delivery_charge


    
    def create_signature(
            self, 
            transaction_uuid=None,
            ) -> str:
        """
        Creates a signature for the payment request.

        Args:
            total_amount (float): The total amount for the transaction.
            transaction_uuid (str): A unique identifier for the transaction.

        Returns:
            str: The generated signature.

        Steps:
            1. Set the amount and UUID attributes.
            2. Generate the signature using the provided parameters.
            3. Return the generated signature.
        """
        total_amount = self.total_amount
        if self.transaction_uuid is None:
            self.transaction_uuid = transaction_uuid
        self.signature = generate_signature(total_amount, self.transaction_uuid, self.secret_key, self.product_code)
        return self.signature

    
    def generate_redirect_url() -> None:
        pass

    def refund_payment() -> None:
        pass

    def simulate_payment() -> None:
        pass

    def generate_form(self) -> str:
        """
        Generates a form for eSewa payment.

        Args:
            None

        Returns:
            str: A HTML code snippet to create a hidden form with necessary fields.
        
        Steps:
            1. Create a payload dictionary with the required fields.
            2. Initialize an empty string for the form.
            3. Iterate over the payload items and append hidden input fields to the form string.
            4. Return the form string.
        """
        payload = {
            "amount": self.amount,
            "product_delivery_charge": self.product_delivery_charge,
            "product_service_charge": self.product_service_charge,
            "total_amount": self.total_amount,
            "tax_amount": self.tax_amount,
            "product_code": self.product_code,
            "transaction_uuid": self.transaction_uuid,
            "success_url": self.success_url,
            "failure_url": self.failure_url,
            "signed_field_names": "total_amount,transaction_uuid,product_code",
            "signature": self.signature
        }

        form= ""
        for key, value in payload.items():
            form += f'<input type="hidden" name="{key}" value="{value}">'
        return form


    def get_status(self, dev: bool) -> str:
        """
        Fetches the transaction status from eSewa.

        Args:
            dev (bool): Use the testing environment if True, production otherwise.

        Returns:
            str: The transaction status.

        Steps:
            1. Constructs the status URL based on the environment (testing or production).
            2. Sends a GET request to the eSewa API.
            3. Checks the response status code.
            4. Parses the JSON response.
            5. Returns the transaction status.
            6. Raises an exception if the request fails.
        """
        status_url_testing = f"https://rc.esewa.com.np/api/epay/transaction/status/?product_code={self.product_code}&total_amount={self.amount}&transaction_uuid={self.transaction_uuid}"
        status_url_prod = f"https://epay.esewa.com.np/api/epay/transaction/status/?product_code={self.product_code}&total_amount={self.amount}&transaction_uuid={self.transaction_uuid}"

        url = status_url_testing if dev else status_url_prod
        response = requests.get(url)

        if response.status_code != 200:
            raise requests.exceptions.RequestException(f"Error fetching status: {response.text}")

        response_data = response.json()
        return response_data.get("status", "UNKNOWN")


    def is_completed(self, dev:bool=False) -> bool:
        """
        Checks if the transaction is completed.

        Args:
            dev (bool): Use the testing environment if True, production otherwise.
        Returns:
            bool: True if the transaction is completed, False otherwise.
        Steps:
            1. Calls the get_status method to fetch the transaction status.
            2. Checks if the status is "COMPLETE".
            3. Returns True if completed, False otherwise.
        """
        return self.get_status(dev) == "COMPLETE"

    def __eq__(self, value: object) -> bool:
        """
        Compare this EsewaPayment instance with another instance for equality.

        Args:
            value (object): The object to compare with.

        Returns:
            bool: True if the given object is an instance of EsewaPayment and has the same
                secret_key and product_code as this instance, False otherwise.

        Steps:
            1. Check if the given object is an instance of EsewaPayment.
            2. Compare the secret_key and product_code attributes.
            3. Return True if both attributes match, False otherwise.
        """
        ''''''
        if not isinstance(value, EsewaPayment):
            return False
        return self.secret_key == value.secret_key and self.product_code == value.product_code
        
    def verify_signature(
            self,
        response_body_base64: str,
    ) -> tuple[bool, dict[str, str] | None]:
        """
        Verifies the signature of an eSewa response.
        
        Args:
            response_body_base64 (str): The Base64-encoded response body.
        
        Returns:
            tuple[bool, dict[str, str] | None]: 
                A tuple where the first element is a boolean indicating the validity of the signature,
                and the second element is a dictionary of the decoded response data if the signature is valid, otherwise None.

        Steps:
            1. Decode the Base64-encoded response body.
            2. Parse the JSON response.
            3. Extract the signed field names and received signature.
            4. Construct the message to be signed.
            5. Compare the received signature with the generated signature.
            6. Return a tuple with the validity and response data if valid, otherwise None.
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
            is_valid: bool = received_signature == self.signature
            return is_valid, response_data if is_valid else None
        except Exception as e:
            print(f"Error verifying signature: {e}")
            return False, None


    def log_transaction(self):
        """
        Logs the transaction details.

        Args:
            None

        Returns:
            None

        Steps:
            1. Get a logger instance.
            2. Log the transaction details.
        """
        logger = logging.getLogger(__name__)
        logger.info({
            "Transaction UUID": self.transaction_uuid,
            "Product Code": self.product_code,
            "Total Amount": self.amount,
            "Signature": self.signature
        })


if __name__ == "__main__":
    payment = EsewaPayment(
        product_code="EPAYTEST",
        success_url="http://localhost:8000/success/",
        failure_url="http://localhost:8000/failure/",
        amount=100,
        tax_amount=0,
        total_amount=100,
        product_service_charge=0,
        product_delivery_charge=0,
        transaction_uuid="11-200-111sss1",
    )
    signature = payment.create_signature()
    print(f"Generated Signature: {signature}")
    payload = payment.generate_form()
    # print(f"Generated Payload: {payload}")
    status = payment.get_status(dev=True)
    # print(f"Transaction Status: {status}")
    completed = payment.is_completed(dev=True)
    # print(f"Transaction Completed: {completed}")
    payment.log_transaction()
    verified, response_data = payment.verify_signature("eyJ0cmFuc2FjdGlvbl9jb2RlIjoiMExENUNFSCIsInN0YXR1cyI6IkNPTVBMRVRFIiwidG90YWxfYW1vdW50IjoiMSwwMDAuMCIsInRyYW5zYWN0aW9uX3V1aWQiOiIyNDA2MTMtMTM0MjMxIiwicHJvZHVjdF9jb2RlIjoiTlAtRVMtQUJISVNIRUstRVBBWSIsInNpZ25lZF9maWVsZF9uYW1lcyI6InRyYW5zYWN0aW9uX2NvZGUsc3RhdHVzLHRvdGFsX2Ftb3VudCx0cmFuc2FjdGlvbl91dWlkLHByb2R1Y3RfY29kZSxzaWduZWRfZmllbGRfbmFtZXMiLCJzaWduYXR1cmUiOiJNcHd5MFRGbEhxcEpqRlVER2ljKzIybWRvZW5JVFQrQ2N6MUxDNjFxTUFjPSJ9 ")



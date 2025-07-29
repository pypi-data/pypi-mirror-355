
from flask import jsonify

from totoapicontroller.TotoTokenVerifier import TokenVerificationResult


class ValidationResult: 
    
    validation_passed: bool
    error_code: int 
    error_message: str
    token_verification_result: TokenVerificationResult
    
    def __init__(self, validation_passed: bool, error_code: int = None, error_message: str = None, cid: str = None, token_verification_result: TokenVerificationResult = None): 
        
        self.validation_passed = validation_passed
        self.error_code = error_code
        self.error_message = error_message
        self.token_verification_result = token_verification_result
        
    def to_flask_response(self): 
        """ Generates a Flask Response out of this validation result 
        
        This method would be typically used to return a validation errors to the caller
        """
        return jsonify({"code": self.error_code, "message": self.error_message}), self.error_code
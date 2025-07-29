# -*- coding: utf-8 -*-


class SupportMfaConfigInfo(object):

    """Implementation of the 'SupportMfaConfigInfo' model.

    Holds the MFA configuration to be returned or stored.

    Attributes:
        email (string): Specifies email address of the support user. Used when MFA mode
          is email.
        enabled (bool): Specifies whether MFA is enabled for support user.
        mfa_code (string): MFA code that needs to be passed when disabling MFA or changing
          email address when email based MFA is configured.
        mfa_type (MfaTypeEnum): Specifies the mechanism to receive the OTP code.
        otp_verification_state (OtpVerificationStateEnum): Specifies the status of otp verification.

    """

    # Create a mapping from Model property names to API property names
    _names = {
        "email":'email',
        "enabled":'enabled',
        "mfa_code":'mfaCode',
        "mfa_type":'mfaType',
        "otp_verification_state":'otpVerificationState'
    }

    def __init__(self,
                 email=None,
                 enabled=None,
                 mfa_code=None,
                 mfa_type=None,
                 otp_verification_state=None):
        """Constructor for the SupportMfaConfigInfo class"""

        # Initialize members of the class
        self.email = email
        self.enabled = enabled
        self.mfa_code = mfa_code
        self.mfa_type = mfa_type
        self.otp_verification_state = otp_verification_state


    @classmethod
    def from_dictionary(cls,
                        dictionary):
        """Creates an instance of this model from a dictionary

        Args:
            dictionary (dictionary): A dictionary representation of the object as
            obtained from the deserialization of the server's response. The keys
            MUST match property names in the API description.

        Returns:
            object: An instance of this structure class.

        """
        if dictionary is None:
            return None

        # Extract variables from the dictionary
        email = dictionary.get('email')
        enabled = dictionary.get('enabled')
        mfa_code = dictionary.get('mfaCode')
        mfa_type = dictionary.get('mfaType')
        otp_verification_state = dictionary.get('otpVerificationState')

        # Return an object of this model
        return cls(email,
                   enabled,
                   mfa_code,
                   mfa_type,
                   otp_verification_state
                   )
#-------------------- Imports --------------------

from rules import *
from mode import Mode
from typing import Optional, Tuple, List, Dict
from typeguard import typechecked

#-------------------- PasswordValidator Object --------------------

@typechecked
class PasswordValidator:
    """
    A flexible and configurable password validator that applies a set of rules
    to check whether a given password meets the defined security criteria.

    The validator can be customized by manually specifying individual rules
    or by selecting a predefined mode (lenient, moderate, or strict).

    Parameters:
    -----------
    min_length : int, optional
        Minimum length required for the password. Default is None.
        
    max_length : int, optional
        Maximum length allowed for the password. Default is None.
        
    require_uppercase : bool, optional
        If True, the password must contain at least one uppercase letter. Default is False.
        
    require_numbers : bool, optional
        If True, the password must contain at least one numeric character. Default is False.
        
    require_symbols : bool, optional
        If True, the password must contain at least one special symbol. Default is False.
        
    no_spaces : bool, optional
        If True, spaces are not allowed in the password. Default is False.
        
    must_include_char : str, optional
        If provided, the password must contain this specific character. Default is None.
        
    no_repeating_chars : int, optional
        Maximum number of allowed consecutive repeating characters. For example,
        if set to 3, "aaa" is valid but "aaaa" is not. Default is None.
        
    blacklisted_pattern : bool, optional
        If True, the password will be checked against a list of blacklisted patterns.
        Default is False.
        
    not_common : bool, optional
        If True, the password must not be one of the most common passwords.
        Default is False.
        
    mode : Mode, optional
        Optional predefined configuration that sets multiple rule parameters at once.
        Available modes:
            - Mode.lenient: Basic length check (8-65 chars), minimal constraints.
            - Mode.moderate: Includes uppercase, numbers, no spaces, limited repetition.
            - Mode.strict: Enforces symbols, blacklist, common password avoidance, and stricter repetition limits.

    Methods:
    --------
    validate(password: str) -> Tuple[bool, List[Dict[str, str]]]
        Validates the given password against all configured rules.
        
        Returns:
            A tuple:
            - A boolean indicating whether the password is valid.
            - A list of dictionaries, each containing:
                - "code": The error code of the failed rule.
                - "message": A human-readable description of the error.
    
    """
    def __init__(
        self,
        min_length: int = None,
        max_length: int = None,
        require_uppercase: bool = False,
        require_numbers: bool = False,
        require_symbols: bool = False,
        no_spaces: bool = False,
        must_include_char: str = None,
        no_repeating_chars: int = None,
        blacklisted_pattern: bool = False,
        not_common: bool = False,
        mode: Optional[Mode] = None
    ):
        
        self.rules = []

        if mode == Mode.lenient:
            min_length = 8
            max_length = 65
            require_uppercase = False
            require_numbers = False
            require_symbols = False
            no_spaces = False
            must_include_char = None
            no_repeating_chars = None
            blacklisted_pattern = False
            not_common = False

        elif mode == Mode.moderate:
            min_length = 8
            max_length = 65
            require_uppercase = True
            require_numbers = True
            require_symbols = False
            no_spaces = True
            must_include_char = None
            no_repeating_chars = 4
            blacklisted_pattern = False
            not_common = False
            
        elif mode == Mode.strict:
            min_length = 12
            max_length = 65
            require_uppercase = True
            require_numbers = True
            require_symbols = True
            no_spaces = True
            must_include_char = None
            no_repeating_chars = 3
            blacklisted_pattern = True
            not_common = True

        if min_length is not None:
            self.rules.append(MinLengthRule(min_length=min_length))
        
        if max_length is not None:
            self.rules.append(MaxLengthRule(max_length=max_length))

        if require_uppercase:
            self.rules.append(UppercaseRule())

        if require_numbers:
            self.rules.append(NumbersRule())

        if require_symbols:
            self.rules.append(SymbolsRule())

        if no_spaces:
            self.rules.append(NoSpacesRule())

        if must_include_char is not None:
            self.rules.append(MustIncludeCharRule(character=must_include_char))

        if no_repeating_chars is not None:
            self.rules.append(NoRepeatingCharsRule(repeating_limit=no_repeating_chars))

        if blacklisted_pattern:
            self.rules.append(BlacklistRule())

        if not_common:
            self.rules.append(MostCommonPasswordsRule())

    def validate(self, password: str = None) -> Tuple[bool, List[Dict[str, str]]]:
        errors = [
            {"code": rule.code, "message": rule.message()}
            for rule in self.rules if not rule.validate(password)
        ]
        return len(errors) == 0, errors

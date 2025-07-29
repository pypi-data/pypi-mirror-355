import re

def validate_cnpj(cnpj: str) -> bool:
    """Valida um CNPJ (Cadastro Nacional de Pessoa Jurídica)."""
    cnpj = re.sub(r'\D', '', cnpj)

    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calc_digit(cnpj_slice, multipliers):
        total = sum(int(d) * m for d, m in zip(cnpj_slice, multipliers))
        digit = 11 - (total % 11)
        return '0' if digit >= 10 else str(digit)

    first_multipliers = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    second_multipliers = [6] + first_multipliers

    first_digit = calc_digit(cnpj[:12], first_multipliers)
    second_digit = calc_digit(cnpj[:13], second_multipliers)

    return cnpj[-2:] == first_digit + second_digit

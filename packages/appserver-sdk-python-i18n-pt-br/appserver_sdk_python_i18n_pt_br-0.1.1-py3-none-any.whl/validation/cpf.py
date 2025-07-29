import re

def validate_cpf(cpf: str) -> bool:
    """Valida um CPF (Cadastro de Pessoa Física)."""
    cpf = re.sub(r'\D', '', cpf)

    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    def calc_digit(cpf_slice, factor):
        total = sum(int(d) * f for d, f in zip(cpf_slice, range(factor, 1, -1)))
        digit = 11 - total % 11
        return '0' if digit >= 10 else str(digit)

    first_digit = calc_digit(cpf[:9], 10)
    second_digit = calc_digit(cpf[:10], 11)

    return cpf[-2:] == first_digit + second_digit

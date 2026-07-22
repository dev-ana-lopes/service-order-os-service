from __future__ import annotations

import re


def normalize_digits(value: str) -> str:
    return re.sub(r"\D", "", value or "")


def is_valid_cpf(value: str) -> bool:
    cpf = normalize_digits(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False

    def calc_digit(base: str, factor: int) -> str:
        total = sum(int(digit) * (factor - index) for index, digit in enumerate(base))
        mod = total % 11
        return "0" if mod < 2 else str(11 - mod)

    first_digit = calc_digit(cpf[:9], 10)
    second_digit = calc_digit(cpf[:10], 11)
    return cpf[-2:] == first_digit + second_digit


def is_valid_cnpj(value: str) -> bool:
    cnpj = normalize_digits(value)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False

    def calc_digit(base: str, weights: list[int]) -> str:
        total = sum(int(digit) * weight for digit, weight in zip(base, weights, strict=False))
        mod = total % 11
        return "0" if mod < 2 else str(11 - mod)

    first_digit = calc_digit(cnpj[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    second_digit = calc_digit(cnpj[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return cnpj[-2:] == first_digit + second_digit


def is_valid_cpf_cnpj(value: str) -> bool:
    digits = normalize_digits(value)
    if len(digits) == 11:
        return is_valid_cpf(digits)
    if len(digits) == 14:
        return is_valid_cnpj(digits)
    return False


def normalize_plate(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", value or "").upper()


def is_valid_br_plate(value: str) -> bool:
    plate = normalize_plate(value)
    return bool(
        re.fullmatch(r"[A-Z]{3}[0-9]{4}", plate)
        or re.fullmatch(r"[A-Z]{3}[0-9][A-Z][0-9]{2}", plate)
    )

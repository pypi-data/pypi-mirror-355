import math
import re
from personnummer import personnummer

string_types = str


class OrganisationsnummerException(Exception):
    pass


class OrganisationsnummerInvalidException(OrganisationsnummerException):
    pass


class OrganisationsnummerParseException(OrganisationsnummerException):
    pass


ORG_TYPES: dict[str, str] = {
    "1": "Dödsbon",
    "2": "Stat, landsting, kommun eller församling",
    "3": "Utländska företag som bedriver näringsverksamhet eller äger fastigheter i Sverige",
    "5": "Aktiebolag",
    "6": "Enkelt bolag",
    "7": "Ekonomisk förening eller bostadsrättsförening",
    "8": "Ideella förening och stiftelse",
    "9": "Handelsbolag, kommanditbolag och enkelt bolag",
}


class Organisationsnummer:
    _personnummer: personnummer.Personnummer | None = None
    _number: str

    def __init__(self, number: str, options=None):
        """
        Initializes the Object and checks if the given Swedish organisation number is valid.
        :param number
        :type number str
        :param options
        :type options dict
        """

        if options is None:
            options = {}

        self.options = options
        self._number = number

        try:
            reg = r"^(\d{2}){0,1}(\d{2})(\d{2})(\d{2})([\-\+]{0,1})?(\d{3})(\d{0,1})$"
            match = re.match(reg, str(object=number))

            if not match:
                raise OrganisationsnummerParseException(
                    f'Could not parse "{number}" as a valid Swedish Organisation Number.'
                )

            number = number.replace("-", "").replace("+", "")

            if match[1]:
                if match[1] != "16":
                    raise OrganisationsnummerInvalidException(
                        f'"{number}" Is not a valid Swedish Organisation Number'
                    )
                else:
                    number = number[2:]

            if int(match[3]) < 20:
                raise OrganisationsnummerInvalidException(
                    f'"{number}" Is not a valid Swedish Organisation Number'
                )

            if match[2][0] == "0":
                raise OrganisationsnummerInvalidException(
                    f'"{number}" Is not a valid Swedish Organisation Number'
                )

            if _luhn(number[:9]) != int(number[9]):
                raise OrganisationsnummerInvalidException(
                    f'"{number}" Is not a valid Swedish Organisation Number'
                )

            self._number = number
        except OrganisationsnummerException as e:
            try:
                self._personnummer = personnummer.Personnummer.parse(self._number)
            except Exception as exc:
                raise e from exc

    def is_personnummer(self):
        """
        Determine if personnummer or not.

        :rtype: bool
        :return:
        """
        return self._personnummer is not None

    def personnummer(self):
        """
        Get Personnummer instance.

        :rtype: Personnummer|None
        :return:
        """
        return self._personnummer

    def format(self, separator=False):
        """
        Format Swedish organization number with or without separator.

        :param long_format: Defaults to True and formats an organisation number
            as NNNNNN-NNNC. If set to False the format will be NNNNNNNNNC.
        :type separator: bool
        :rtype: str
        :return:
        """

        if self.is_personnummer():
            return self._personnummer.format(not separator)[(0 if separator else 2) :]

        return f"{self._number[:6]}-{self._number[6:]}" if separator else self._number

    def type(self):
        if self.is_personnummer():
            return "Enskild firma"

        return ORG_TYPES.get(self._number[0], "Okänt")

    def vat_number(self):
        return f"SE{self.format()}01"

    @staticmethod
    def parse(number, options=None):
        """
        Returns a new Organisationsnummer object
        :param number
        :type number str/int
        :param options
        :type options dict
        :rtype: Organisationsnummer
        :return:
        """
        return Organisationsnummer(number, options)


def _luhn(data):
    """
    Calculates the Luhn checksum of a string of digits
    :param data
    :type data str
    :rtype: int
    :return:
    """
    calculation = 0

    for i in range(len(data)):
        v = int(data[i])
        v *= 2 - (i % 2)
        if v > 9:
            v -= 9
        calculation += v

    return int(math.ceil(float(calculation) / 10) * 10 - float(calculation))


def parse(number, options=None):
    """
    Returns a new Organisationsnummer object
    :param number
    :type number str/int
    :param options
    :type options dict
    :rtype: Organisationsnummer
    :return:
    """
    return Organisationsnummer.parse(number, options)


def valid(number):
    """
    Checks if a ssn is a valid Swedish organisation number
    :param number A Swedish organisation number
    :type number str/int
    """
    try:
        parse(number)
        return True
    except OrganisationsnummerException:
        return False

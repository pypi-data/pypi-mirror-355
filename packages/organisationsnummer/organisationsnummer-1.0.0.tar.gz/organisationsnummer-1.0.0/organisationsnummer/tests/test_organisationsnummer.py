from unittest import TestCase

from personnummer import personnummer

from organisationsnummer import organisationsnummer
import urllib.request
import json


def get_test_data():
    response = urllib.request.urlopen(
        "https://raw.githubusercontent.com/organisationsnummer/meta/main/testdata/list.json"
    )
    raw = response.read().decode("utf-8")
    return json.loads(raw)


test_data = get_test_data()
availableListFormats = [
    "long_format",
    "short_format",
]


class TestOrganisationsnummer(TestCase):
    def testOrganisationsnummerList(self):
        for item in test_data:
            for available_format in availableListFormats:
                self.assertEqual(
                    organisationsnummer.valid(item[available_format]), item["valid"]
                )

    def testOrganisationsnummerFormat(self):
        for item in test_data:
            if not item["valid"]:
                continue

            expected_long_format = item["long_format"]
            expected_short_format = item["short_format"]
            for available_format in availableListFormats:
                if available_format == "short_format" and "+" in expected_long_format:
                    # Since the short format is missing the separator,
                    # the library will never use the `+` separator
                    # in the outputted format
                    continue
                self.assertEqual(
                    expected_short_format,
                    organisationsnummer.parse(item[available_format]).format(),
                )
                self.assertEqual(
                    expected_long_format,
                    organisationsnummer.parse(item[available_format]).format(True),
                )

    def testOrganisationsnummerError(self):
        for item in test_data:
            if item["valid"]:
                continue

            for available_format in availableListFormats:
                self.assertRaises(
                    organisationsnummer.OrganisationsnummerException,
                    organisationsnummer.parse,
                    item[available_format],
                )

    def testOrganisationsnummerType(self):
        for item in test_data:
            if not item["valid"]:
                continue

            for available_format in availableListFormats:
                self.assertEqual(
                    organisationsnummer.parse(item[available_format]).type(),
                    item["type"],
                )

    def testOrganisationsnummerPersonnummer(self):
        for item in test_data:
            if not item["valid"]:
                continue

            for available_format in availableListFormats:
                self.assertEqual(
                    organisationsnummer.parse(item[available_format]).is_personnummer(),
                    item["type"] == "Enskild firma",
                )
                if item["type"] == "Enskild firma":
                    self.assertIsInstance(
                        organisationsnummer.parse(
                            item[available_format]
                        ).personnummer(),
                        personnummer.Personnummer,
                    )

    def testOrganisationsnummerVatNumber(self):
        for item in test_data:
            if not item["valid"]:
                continue

            for available_format in availableListFormats:
                self.assertEqual(
                    organisationsnummer.parse(item[available_format]).vat_number(),
                    item["vat_number"],
                )

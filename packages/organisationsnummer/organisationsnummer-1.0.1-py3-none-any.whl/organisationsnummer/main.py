import argparse

from organisationsnummer import organisationsnummer
from organisationsnummer.organisationsnummer import OrganisationsnummerException


def setup_args():
    ap = argparse.ArgumentParser("organisationsnummer")
    ap.add_argument("onr")
    return ap


def main():
    ap = setup_args()
    args = ap.parse_args()
    if args.pnr:
        try:
            on = organisationsnummer.Organisationsnummer(args.onr)

            print(f"Organisationsnummer: {on.format()}")
            print(f"Type: {on.type()}")

        except OrganisationsnummerException:
            print("Not a valid Swedish organisation number")

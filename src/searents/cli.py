"""Command-line Interface"""

import argparse
import logging
import os
import re
import sqlite3
import sys
import time
from typing import Any, List, Optional

import dateutil.parser

import searents
from searents.survey import RentListing, RentSurvey
from searents.equity import EquityScraper


def database_connection(*args: Any, **kwargs: Any) -> sqlite3.Connection:
    """Create a connection to the database."""
    kwargs["detect_types"] = sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
    sqlite3.register_converter("TIMESTAMP", dateutil.parser.parse)
    connection = sqlite3.connect(*args, **kwargs)
    connection.row_factory = sqlite3.Row
    connection.execute(
        "CREATE TABLE IF NOT EXISTS listings"
        "(timestamp TIMESTAMP, url TEXT, scraper TEXT, unit TEXT, price REAL)",
    )
    connection.commit()
    return connection


def fetch_handler(
    args: argparse.Namespace,
    scrapers: List[EquityScraper],
    connection: sqlite3.Connection,
) -> None:
    """Fetch new listings."""
    for scraper in scrapers:

        logging.info("Fetching new listings from %s...", scraper.name)
        survey = scraper.scrape_survey()

        logging.info("%d new listings were fetched.", len(survey.listings))
        if survey.listings:
            print(survey)

            logging.info(
                "Writing the new listings to the database at %s...",
                args.database,
            )
            connection.executemany(
                "INSERT INTO listings VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        listing.timestamp,
                        listing.url,
                        scraper.name,
                        listing.unit,
                        listing.price,
                    )
                    for listing in survey.listings
                ],
            )
            connection.commit()


def regenerate_handler(
    args: argparse.Namespace,
    scrapers: List[EquityScraper],
    connection: sqlite3.Connection,
) -> None:
    """Create a database from the scrape cache."""
    logging.info("Recreating the database at %s...", args.database)
    connection.close()
    if os.path.exists(args.database):
        os.rename(args.database, args.database + "." + str(time.time()))
    connection = database_connection(args.database)

    for scraper in scrapers:

        logging.info("Generating a survey from the cache at %s...", scraper.cache_path)
        survey = scraper.cache_survey

        logging.info("Writing the %s survey to the database...", scraper.name)
        connection.executemany(
            "INSERT INTO listings VALUES (?, ?, ?, ?, ?)",
            [
                (
                    listing.timestamp,
                    listing.url,
                    scraper.name,
                    listing.unit,
                    listing.price,
                )
                for listing in survey.listings
            ],
        )
        connection.commit()

    connection.close()
    sys.exit()


def show_handler(
    args: argparse.Namespace,
    scrapers: List[EquityScraper],
    connection: sqlite3.Connection,
) -> None:
    """Show listings."""
    survey = RentSurvey()
    for scraper in scrapers:
        logging.info(
            "Reading %s listings from the database at %s...",
            scraper.name,
            args.database,
        )
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM listings WHERE scraper=?", (scraper.name,))
        survey.listings.extend(
            RentListing(**listing)
            for listing in (dict(row) for row in cursor.fetchall())
            if any(
                all(
                    [
                        re.search(args.filter_key, str(key)) is not None,
                        re.search(args.filter, str(value)) is not None,
                    ],
                )
                for key, value in listing.items()
            )
        )
    if survey.listings:
        logging.info("Showing %s listings...", len(survey.listings))
        if args.graphical:
            survey.visualize(", ".join(scraper.name for scraper in scrapers))
        else:
            print(survey)


def verify_handler(
    args: argparse.Namespace,
    scrapers: List[EquityScraper],
    connection: sqlite3.Connection,
) -> int:
    """Verify the database against the scrape cache."""
    for scraper in scrapers:

        logging.info(
            "Reading %s listings from the database at %s...",
            scraper.name,
            args.database,
        )
        cursor = connection.execute(
            "SELECT * FROM listings WHERE scraper=?",
            (scraper.name,),
        )
        survey = RentSurvey(listings=[RentListing(**row) for row in cursor.fetchall()])

        logging.info("Generating a survey from the cache at %s...", scraper.cache_path)
        cache_survey = scraper.cache_survey

        logging.info("Verifying the %s survey...", scraper.name)
        if survey != cache_survey:
            return 1

    return 0


def cli(parser: Optional[argparse.ArgumentParser] = None) -> argparse.ArgumentParser:
    """Parse CLI arguments and options."""
    if parser is None:
        parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        )

    parser.add_argument(
        "--cache",
        "-c",
        help="Specify the directory to store scrape caches in.",
        default=os.path.join("{directory}", "cache"),
    )
    parser.add_argument(
        "--directory",
        help="Specify a directory to store a cache, database, and log in.",
        default=os.path.join(os.environ.get("HOME", ""), ".searents"),
    )
    parser.add_argument(
        "--database",
        help="Specify a SeaRents database.",
        default=os.path.join("{directory}", "searents.db"),
    )
    parser.add_argument(
        "--log-file",
        help="Specify the file to log to.",
        default=os.path.join("{directory}", "searents.log"),
    )
    parser.add_argument(
        "--log-level",
        help="Specify a log-level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
        default="INFO",
    )
    parser.add_argument(
        "--scraper",
        help="Specify a search pattern for scraper names.",
        default=".*",
    )
    parser.add_argument("--version", action="version", version=searents.__version__)

    subparsers = parser.add_subparsers()

    fetch_parser = subparsers.add_parser(
        "fetch",
        help=fetch_handler.__doc__,
    )
    fetch_parser.set_defaults(func=fetch_handler)

    regenerate_parser = subparsers.add_parser(
        "regenerate",
        help=regenerate_handler.__doc__,
    )
    regenerate_parser.set_defaults(func=regenerate_handler)

    show_parser = subparsers.add_parser(
        "show",
        help=show_handler.__doc__,
    )
    show_parser.add_argument(
        "--filter",
        "-f",
        help="Specify a regex to filter listings.",
        default=".*",
    )
    show_parser.add_argument(
        "--filter-key",
        "-k",
        help="Specify a regex to filter listings by key.",
        default=".*",
    )
    show_parser.add_argument(
        "--graphical",
        "-g",
        help="Plot listings.",
        default=False,
        action="store_true",
    )
    show_parser.set_defaults(func=show_handler)

    verify_parser = subparsers.add_parser(
        "verify",
        help=verify_handler.__doc__,
    )
    verify_parser.set_defaults(func=verify_handler)

    return parser


def main(args: Optional[argparse.Namespace] = None) -> int:
    """Execute CLI commands."""
    if args is None:
        args = cli().parse_args()

    os.makedirs(args.directory, exist_ok=True)
    args.cache = args.cache.format(directory=args.directory)
    args.database = args.database.format(directory=args.directory)
    args.log_file = args.log_file.format(directory=args.directory)

    log_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(log_level, int):
        raise ValueError("Invalid log level: %s" % args.log_level)
    logging.basicConfig(
        filename=args.log_file,
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    equity_url = "http://www.equityapartments.com"
    # pylint: disable=line-too-long
    scrapers = [
        EquityScraper(
            name="One Henry Adams",
            url=equity_url
            + "/san-francisco/design-district/one-henry-adams-apartments",
            cache_path=os.path.join(args.cache, "One_Henry_Adams"),
        ),
        EquityScraper(
            name="Potrero 1010",
            url=equity_url + "/san-francisco/potrero-hill/potrero-1010-apartments",
            cache_path=os.path.join(args.cache, "Potrero_1010"),
        ),
        EquityScraper(
            name="340 Fremont",
            url=equity_url + "/san-francisco/rincon-hill/340-fremont-apartments",
            cache_path=os.path.join(args.cache, "340_Fremont"),
        ),
        EquityScraper(
            name="855 Brannan",
            url=equity_url + "/san-francisco/soma/855-brannan-apartments",
            cache_path=os.path.join(args.cache, "855_Brannan"),
        ),
        EquityScraper(
            name="Acton Courtyard",
            url=equity_url
            + "/san-francisco-bay/berkeley/berkeley-apartments-acton-courtyard",
            cache_path=os.path.join(args.cache, "Acton_Courtyard"),
        ),
        EquityScraper(
            name="ARTech",
            url=equity_url + "/san-francisco-bay/berkeley/berkeley-apartments-artech",
            cache_path=os.path.join(args.cache, "ARTech"),
        ),
        EquityScraper(
            name="Berkeleyan",
            url=equity_url
            + "/san-francisco-bay/berkeley/berkeley-apartments-berkeleyan",
            cache_path=os.path.join(args.cache, "Berkeleyan"),
        ),
        EquityScraper(
            name="Fine Arts",
            url=equity_url
            + "/san-francisco-bay/berkeley/berkeley-apartments-fine-arts",
            cache_path=os.path.join(args.cache, "Fine_Arts"),
        ),
        EquityScraper(
            name="Gaia",
            url=equity_url + "/san-francisco-bay/berkeley/berkeley-apartments-gaia",
            cache_path=os.path.join(args.cache, "Gaia"),
        ),
        EquityScraper(
            name="Renaissance Villas",
            url=equity_url
            + "/san-francisco-bay/berkeley/berkeley-apartments-renaissance-villas",
            cache_path=os.path.join(args.cache, "Renaissance_Villas"),
        ),
        EquityScraper(
            name="Touriel",
            url=equity_url + "/san-francisco-bay/berkeley/berkeley-apartments-touriel",
            cache_path=os.path.join(args.cache, "Touriel"),
        ),
        EquityScraper(
            name="Northpark",
            url=equity_url + "/san-francisco-bay/burlingame/northpark-apartments",
            cache_path=os.path.join(args.cache, "Northpark"),
        ),
        EquityScraper(
            name="Skyline Terrace",
            url=equity_url + "/san-francisco-bay/burlingame/skyline-terrace-apartments",
            cache_path=os.path.join(args.cache, "Skyline_Terrace"),
        ),
        EquityScraper(
            name="Woodleaf",
            url=equity_url + "/san-francisco-bay/campbell/woodleaf-apartments",
            cache_path=os.path.join(args.cache, "Woodleaf"),
        ),
        EquityScraper(
            name="La Terrazza",
            url=equity_url + "/san-francisco-bay/colma/la-terrazza-apartments",
            cache_path=os.path.join(args.cache, "La_Terrazza"),
        ),
        EquityScraper(
            name="City Gate at Cupertino",
            url=equity_url
            + "/san-francisco-bay/cupertino/city-gate-at-cupertino-apartments",
            cache_path=os.path.join(args.cache, "City_Gate_at_Cupertino"),
        ),
        EquityScraper(
            name="88 Hillside",
            url=equity_url + "/san-francisco-bay/daly-city/88-hillside-apartments",
            cache_path=os.path.join(args.cache, "88_Hillside"),
        ),
        EquityScraper(
            name="Geary Courtyard",
            url=equity_url
            + "/san-francisco-bay/downtown-san-francisco/geary-courtyard-apartments",
            cache_path=os.path.join(args.cache, "Geary_Courtyard"),
        ),
        EquityScraper(
            name="Fountains at Emerald Park",
            url=equity_url
            + "/san-francisco-bay/dublin/fountains-at-emerald-park-apartments",
            cache_path=os.path.join(args.cache, "Fountains_at_Emerald_Park"),
        ),
        EquityScraper(
            name="Artistry Emeryville",
            url=equity_url
            + "/san-francisco-bay/emeryville/artistry-emeryville-apartments",
            cache_path=os.path.join(args.cache, "Artistry_Emeryville"),
        ),
        EquityScraper(
            name="Parc on Powell",
            url=equity_url + "/san-francisco-bay/emeryville/parc-on-powell-apartments",
            cache_path=os.path.join(args.cache, "Parc_on_Powell"),
        ),
        EquityScraper(
            name="Lantern Cove",
            url=equity_url + "/san-francisco-bay/foster-city/lantern-cove-apartments",
            cache_path=os.path.join(args.cache, "Lantern_Cove"),
        ),
        EquityScraper(
            name="Schooner Bay Apartment Homes",
            url=equity_url
            + "/san-francisco-bay/foster-city/schooner-bay-apartment-homes",
            cache_path=os.path.join(args.cache, "Schooner_Bay_Apartment_Homes"),
        ),
        EquityScraper(
            name="Alborada",
            url=equity_url + "/san-francisco-bay/fremont/alborada-apartments",
            cache_path=os.path.join(args.cache, "Alborada"),
        ),
        EquityScraper(
            name="Archstone Fremont Center",
            url=equity_url
            + "/san-francisco-bay/fremont/archstone-fremont-center-apartments",
            cache_path=os.path.join(args.cache, "Archstone_Fremont_Center"),
        ),
        EquityScraper(
            name="The Terraces",
            url=equity_url
            + "/san-francisco-bay/lower-nob-hill/the-terraces-apartments",
            cache_path=os.path.join(args.cache, "The_Terraces"),
        ),
        EquityScraper(
            name="Mill Creek",
            url=equity_url + "/san-francisco-bay/milpitas/mill-creek-apartments",
            cache_path=os.path.join(args.cache, "Mill_Creek"),
        ),
        EquityScraper(
            name="Azure",
            url=equity_url + "/san-francisco-bay/mission-bay/azure-apartments",
            cache_path=os.path.join(args.cache, "Azure"),
        ),
        EquityScraper(
            name="Reserve at Mountain View",
            url=equity_url
            + "/san-francisco-bay/mountain-view/reserve-at-mountain-view-apartments",
            cache_path=os.path.join(args.cache, "Reserve_at_Mountain_View"),
        ),
        EquityScraper(
            name="Domain",
            url=equity_url + "/san-francisco-bay/north-san-jose/domain-apartments",
            cache_path=os.path.join(args.cache, "Domain"),
        ),
        EquityScraper(
            name="Vista 99",
            url=equity_url + "/san-francisco-bay/north-san-jose/vista-99-apartments",
            cache_path=os.path.join(args.cache, "Vista_99"),
        ),
        EquityScraper(
            name="Southwood",
            url=equity_url + "/san-francisco-bay/palo-alto/southwood-apartments",
            cache_path=os.path.join(args.cache, "Southwood"),
        ),
        EquityScraper(
            name="Northridge",
            url=equity_url + "/san-francisco-bay/pleasant-hill/northridge-apartments",
            cache_path=os.path.join(args.cache, "Northridge"),
        ),
        EquityScraper(
            name="Wood Creek",
            url=equity_url
            + "/san-francisco-bay/pleasant-hill/wood-creek-ca-apartments",
            cache_path=os.path.join(args.cache, "Wood_Creek"),
        ),
        EquityScraper(
            name="Park Hacienda",
            url=equity_url + "/san-francisco-bay/pleasanton/park-hacienda-apartments",
            cache_path=os.path.join(args.cache, "Park_Hacienda"),
        ),
        EquityScraper(
            name="Avenue Two",
            url=equity_url + "/san-francisco-bay/redwood-city/avenue-two-apartments",
            cache_path=os.path.join(args.cache, "Avenue_Two"),
        ),
        EquityScraper(
            name="Riva Terra Apartments at Redwood Shores",
            url=equity_url
            + "/san-francisco-bay/redwood-city/riva-terra-apartments-at-redwood-shores",
            cache_path=os.path.join(
                args.cache,
                "Riva_Terra_Apartments_at_Redwood_Shores",
            ),
        ),
        EquityScraper(
            name="Verde",
            url=equity_url + "/san-francisco-bay/san-jose/verde-apartments",
            cache_path=os.path.join(args.cache, "Verde"),
        ),
        EquityScraper(
            name="55 West Fifth",
            url=equity_url + "/san-francisco-bay/san-mateo/55-west-fifth-apartments",
            cache_path=os.path.join(args.cache, "55_West_Fifth"),
        ),
        EquityScraper(
            name="Creekside",
            url=equity_url + "/san-francisco-bay/san-mateo/creekside-apartments",
            cache_path=os.path.join(args.cache, "Creekside"),
        ),
        EquityScraper(
            name="Park Place at San Mateo",
            url=equity_url
            + "/san-francisco-bay/san-mateo/park-place-at-san-mateo-apartments",
            cache_path=os.path.join(args.cache, "Park_Place_at_San_Mateo"),
        ),
        EquityScraper(
            name="Canyon Creek",
            url=equity_url + "/san-francisco-bay/san-ramon/canyon-creek-ca-apartments",
            cache_path=os.path.join(args.cache, "Canyon_Creek"),
        ),
        EquityScraper(
            name="Estancia at Santa Clara",
            url=equity_url
            + "/san-francisco-bay/santa-clara/estancia-at-santa-clara-apartments",
            cache_path=os.path.join(args.cache, "Estancia_at_Santa_Clara"),
        ),
        EquityScraper(
            name="Laguna Clara",
            url=equity_url + "/san-francisco-bay/santa-clara/laguna-clara-apartments",
            cache_path=os.path.join(args.cache, "Laguna_Clara"),
        ),
        EquityScraper(
            name="Summit at Sausalito",
            url=equity_url
            + "/san-francisco-bay/sausalito/summit-at-sausalito-apartments",
            cache_path=os.path.join(args.cache, "Summit_at_Sausalito"),
        ),
        EquityScraper(
            name="77 Bluxome",
            url=equity_url + "/san-francisco-bay/soma/77-bluxome-apartments",
            cache_path=os.path.join(args.cache, "77_Bluxome"),
        ),
        EquityScraper(
            name="SoMa Square",
            url=equity_url + "/san-francisco-bay/soma/soma-square-apartments",
            cache_path=os.path.join(args.cache, "SoMa_Square"),
        ),
        EquityScraper(
            name="South City Station",
            url=equity_url
            + "/san-francisco-bay/south-san-francisco/south-city-station-apartments",
            cache_path=os.path.join(args.cache, "South_City_Station"),
        ),
        EquityScraper(
            name="Arbor Terrace",
            url=equity_url + "/san-francisco-bay/sunnyvale/arbor-terrace-apartments",
            cache_path=os.path.join(args.cache, "Arbor_Terrace"),
        ),
        EquityScraper(
            name="Briarwood",
            url=equity_url + "/san-francisco-bay/sunnyvale/briarwood-apartments",
            cache_path=os.path.join(args.cache, "Briarwood"),
        ),
        EquityScraper(
            name="The Arches",
            url=equity_url + "/san-francisco-bay/sunnyvale/the-arches-apartments",
            cache_path=os.path.join(args.cache, "The_Arches"),
        ),
        EquityScraper(
            name="Parkside",
            url=equity_url + "/san-francisco-bay/union-city/parkside-apartments",
            cache_path=os.path.join(args.cache, "Parkside"),
        ),
        EquityScraper(
            name="Skylark",
            url=equity_url + "/san-francisco-bay/union-city/skylark-apartments",
            cache_path=os.path.join(args.cache, "Skylark"),
        ),
        EquityScraper(
            name="Springline",
            url=equity_url + "/seattle/admiral-district/springline-apartments",
            cache_path=os.path.join(args.cache, "Springline"),
        ),
        EquityScraper(
            name="Odin",
            url=equity_url + "/seattle/ballard/odin-apartments",
            cache_path=os.path.join(args.cache, "Odin"),
        ),
        EquityScraper(
            name="Urbana",
            url=equity_url + "/seattle/ballard/urbana-apartments",
            cache_path=os.path.join(args.cache, "Urbana"),
        ),
        EquityScraper(
            name="2300 Elliott",
            url=equity_url + "/seattle/belltown/2300-elliott-apartments",
            cache_path=os.path.join(args.cache, "2300_Elliott"),
        ),
        EquityScraper(
            name="Centennial Tower and Court",
            url=equity_url + "/seattle/belltown/centennial-tower-and-court-apartments",
            cache_path=os.path.join(args.cache, "Centennial_Tower_and_Court"),
        ),
        EquityScraper(
            name="Moda",
            url=equity_url + "/seattle/belltown/moda-apartments",
            cache_path=os.path.join(args.cache, "Moda"),
        ),
        EquityScraper(
            name="Olympus",
            url=equity_url + "/seattle/belltown/olympus-apartments",
            cache_path=os.path.join(args.cache, "Olympus"),
        ),
        EquityScraper(
            name="Ivorywood",
            url=equity_url + "/seattle/bothell/ivorywood-apartments",
            cache_path=os.path.join(args.cache, "Ivorywood"),
        ),
        EquityScraper(
            name="Providence",
            url=equity_url + "/seattle/bothell/providence-apartments",
            cache_path=os.path.join(args.cache, "Providence"),
        ),
        EquityScraper(
            name="Packard Building",
            url=equity_url + "/seattle/capitiol-hill/packard-building-apartments",
            cache_path=os.path.join(args.cache, "Packard_Building"),
        ),
        EquityScraper(
            name="The Pearl",
            url=equity_url + "/seattle/capitiol-hill/the-pearl-apartments-capitol-hill",
            cache_path=os.path.join(args.cache, "The_Pearl"),
        ),
        EquityScraper(
            name="Rianna",
            url=equity_url + "/seattle/capitol-hill/rianna-apartments",
            cache_path=os.path.join(args.cache, "Rianna"),
        ),
        EquityScraper(
            name="The Heights on Capitol Hill",
            url=equity_url
            + "/seattle/capitol-hill/the-heights-on-capitol-hill-apartments",
            cache_path=os.path.join(args.cache, "The_Heights_on_Capitol_Hill"),
        ),
        EquityScraper(
            name="Three20",
            url=equity_url + "/seattle/capitol-hill/three20-apartments",
            cache_path=os.path.join(args.cache, "Three20"),
        ),
        EquityScraper(
            name="City Square Bellevue",
            url=equity_url
            + "/seattle/downtown-bellevue/city-square-bellevue-apartments",
            cache_path=os.path.join(args.cache, "City_Square_Bellevue"),
        ),
        EquityScraper(
            name="Venn at Main",
            url=equity_url + "/seattle/downtown-bellevue/venn-at-main-apartments",
            cache_path=os.path.join(args.cache, "Venn_at_Main"),
        ),
        EquityScraper(
            name="Chelsea Square",
            url=equity_url + "/seattle/downtown-redmond/chelsea-square-apartments",
            cache_path=os.path.join(args.cache, "Chelsea_Square"),
        ),
        EquityScraper(
            name="Old Town Lofts",
            url=equity_url + "/seattle/downtown-redmond/old-town-lofts-apartments",
            cache_path=os.path.join(args.cache, "Old_Town_Lofts"),
        ),
        EquityScraper(
            name="Red160",
            url=equity_url + "/seattle/downtown-redmond/red160-apartments",
            cache_path=os.path.join(args.cache, "Red160"),
        ),
        EquityScraper(
            name="Riverpark",
            url=equity_url + "/seattle/downtown-redmond/riverpark-apartments",
            cache_path=os.path.join(args.cache, "Riverpark"),
        ),
        EquityScraper(
            name="Veloce",
            url=equity_url + "/seattle/downtown-redmond/veloce-apartments",
            cache_path=os.path.join(args.cache, "Veloce"),
        ),
        EquityScraper(
            name="Harbor Steps",
            url=equity_url + "/seattle/downtown-seattle/harbor-steps-apartments",
            cache_path=os.path.join(args.cache, "Harbor_Steps"),
        ),
        EquityScraper(
            name="Helios",
            url=equity_url + "/seattle/downtown-seattle/helios-apartments",
            cache_path=os.path.join(args.cache, "Helios"),
        ),
        EquityScraper(
            name="Surrey Downs",
            url=equity_url + "/seattle/factoria/surrey-downs-apartments",
            cache_path=os.path.join(args.cache, "Surrey_Downs"),
        ),
        EquityScraper(
            name="Seventh and James",
            url=equity_url + "/seattle/first-hill/seventh-and-james-apartments",
            cache_path=os.path.join(args.cache, "Seventh_and_James"),
        ),
        EquityScraper(
            name="Uwajimaya Village",
            url=equity_url
            + "/seattle/international-district/uwajimaya-village-apartments",
            cache_path=os.path.join(args.cache, "Uwajimaya_Village"),
        ),
        EquityScraper(
            name="Harrison Square",
            url=equity_url + "/seattle/lower-queen-anne/harrison-square-apartments",
            cache_path=os.path.join(args.cache, "Harrison_Square"),
        ),
        EquityScraper(
            name="Metro on First",
            url=equity_url + "/seattle/lower-queen-anne/metro-on-first-apartments",
            cache_path=os.path.join(args.cache, "Metro_on_First"),
        ),
        EquityScraper(
            name="Heritage Ridge",
            url=equity_url + "/seattle/lynnwood/heritage-ridge-apartments",
            cache_path=os.path.join(args.cache, "Heritage_Ridge"),
        ),
        EquityScraper(
            name="Monterra in Mill Creek",
            url=equity_url + "/seattle/mill-creek/monterra-in-mill-creek-apartments",
            cache_path=os.path.join(args.cache, "Monterra_in_Mill_Creek"),
        ),
        EquityScraper(
            name="The Reserve at Town Center",
            url=equity_url
            + "/seattle/mill-creek/the-reserve-at-town-center-apartments",
            cache_path=os.path.join(args.cache, "The_Reserve_at_Town_Center"),
        ),
        EquityScraper(
            name="Bellevue Meadows",
            url=equity_url + "/seattle/redmond/bellevue-meadows-apartments",
            cache_path=os.path.join(args.cache, "Bellevue_Meadows"),
        ),
        EquityScraper(
            name="Redmond Court",
            url=equity_url + "/seattle/redmond/redmond-court-apartments",
            cache_path=os.path.join(args.cache, "Redmond_Court"),
        ),
        EquityScraper(
            name="Square One",
            url=equity_url + "/seattle/roosevelt/square-one-apartments",
            cache_path=os.path.join(args.cache, "Square_One"),
        ),
        EquityScraper(
            name="Alcyone",
            url=equity_url + "/seattle/south-lake-union/alcyone-apartments",
            cache_path=os.path.join(args.cache, "Alcyone"),
        ),
        EquityScraper(
            name="Cascade",
            url=equity_url + "/seattle/south-lake-union/cascade-apartments",
            cache_path=os.path.join(args.cache, "Cascade"),
        ),
        EquityScraper(
            name="Junction 47",
            url=equity_url + "/seattle/west-seattle/junction-47-apartments",
            cache_path=os.path.join(args.cache, "Junction_47"),
        ),
    ]
    # pylint: enable=line-too-long

    connection = database_connection(args.database)
    status = args.func(
        args,
        [
            scraper
            for scraper in scrapers
            if re.search(args.scraper, scraper.name) is not None
        ],
        connection,
    )
    connection.close()
    return int(status or 0)

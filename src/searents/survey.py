"""Structures for Tracking Listings"""

import datetime

try:
    import matplotlib
    from matplotlib import pyplot
    from matplotlib.pyplot import cm
    import numpy
except ImportError:

    def _visualize(self, name=None):
        raise NotImplementedError("The visualizer dependencies are not installed.")


else:

    def _visualize(self, name=None):
        """Plot listings."""
        if not self.listings:
            return
        urls = {listing["url"] for listing in self.listings}
        distinct_units = len(
            {listing["url"] + listing["unit"] for listing in self.listings},
        )
        url_colors = iter(
            cm.rainbow(numpy.linspace(0, 1, len(urls))),  # pylint: disable=no-member
        )
        unit_colors = iter(
            cm.rainbow(  # pylint: disable=no-member
                numpy.linspace(0, 1, distinct_units),
            ),
        )
        labelled = set()
        for _, unit_episodes in self.url_episodes():
            url_color = next(url_colors)
            for unit, episodes in unit_episodes:
                unit_color = next(unit_colors)
                for episode in episodes:
                    label = episode[-1]["scraper"] if len(urls) > 1 else unit
                    pyplot.plot_date(
                        matplotlib.dates.date2num(
                            [listing["timestamp"] for listing in episode],
                        ),
                        [listing["price"] for listing in episode],
                        "b-",
                        color=url_color if len(urls) > 1 else unit_color,
                        label=label if label not in labelled else "",
                        linewidth=2,
                    )
                    labelled.add(label)
                    pyplot.text(
                        matplotlib.dates.date2num([episode[-1]["timestamp"]]),
                        episode[-1]["price"],
                        "{0} ({1})".format(unit, episode[-1]["price"]),
                    )
        if name is not None:
            pyplot.gcf().canvas.set_window_title(name)
        pyplot.title("Apartment Prices Over Time")
        pyplot.xlabel("Time")
        pyplot.ylabel("Price")
        pyplot.grid(b=True, which="major", color="k", linestyle="-")
        pyplot.grid(b=True, which="minor", color="k", linestyle=":")
        pyplot.minorticks_on()
        if len(urls) > 1:
            pyplot.legend(loc="upper left")
        pyplot.show()


class RentSurvey:
    """A Collection of Listings"""

    default_threshold = datetime.timedelta(weeks=1)
    listing_types = {
        "price": float,
        "scraper": str,
        "timestamp": datetime.datetime,
        "unit": str,
        "url": str,
    }

    def __init__(self, listings=None):
        """Initialize listings."""
        self.listings = [] if listings is None else listings

    def __str__(self):
        """String-ify collected listings."""
        return "\n".join(
            "[{timestamp}] ${price:,.2f} {scraper} {unit}".format(
                price=listing["price"],
                scraper=listing["scraper"],
                timestamp=listing["timestamp"],
                unit=listing["unit"],
            )
            for listing in self.listings
        )

    def __eq__(self, other):
        """Check equality."""
        try:
            if len(self.listings) != len(other.listings):
                return False
        except (AttributeError, TypeError):
            return False
        return all(
            all(self_listing[key] == other_listing[key] for key in self.listing_types)
            for self_listing, other_listing in zip(
                sorted(self.listings, key=lambda listing: listing["timestamp"]),
                sorted(other.listings, key=lambda listing: listing["timestamp"]),
            )
        )

    def episodes(self, threshold=default_threshold):
        """
        Generate lists of related listings.

        Related listings share url (==), unit (==), and
        timestamp (within a threshold of the previous listing).
        """
        for url in {listing["url"] for listing in self.listings}:
            url_listings = [
                listing for listing in self.listings if listing["url"] == url
            ]
            for unit in sorted({listing["unit"] for listing in url_listings}):
                unit_listings = sorted(
                    (listing for listing in url_listings if listing["unit"] == unit),
                    key=lambda listing: listing["timestamp"],
                )
                episode = unit_listings[0]
                for listing in unit_listings[1:]:
                    if listing["timestamp"] - episode[-1]["timestamp"] > threshold:
                        yield episode
                        episode = []
                    episode.append(listing)
                yield episode

    def is_valid(self):
        """Verify all contained listings are well-formed."""
        return all(
            all(
                isinstance(listing[key], type_)
                for key, type_ in self.listing_types.items()
            )
            for listing in self.listings
        )

    def unit_episodes(self, *args, **kwargs):
        """Generate tuples consisting of a unit and its episodes, respectively."""
        iterator = iter(self.episodes(*args, **kwargs))
        try:
            episodes = [next(iterator)]
        except StopIteration as exc:
            raise RuntimeError("This should never happen.") from exc
        unit = episodes[-1][-1]["unit"]
        for episode in iterator:
            if episode[-1]["unit"] != unit:
                yield unit, episodes
                unit, episodes = episode[-1]["unit"], []
            episodes.append(episode)
        yield unit, episodes

    def url_episodes(self, *args, **kwargs):
        """
        Generate (url, unit_episodes) tuples.

        unit_episodes is a list of units and their episodes, respectively.
        """
        iterator = iter(self.unit_episodes(*args, **kwargs))
        try:
            unit_episodes = [next(iterator)]
        except StopIteration as exc:
            raise RuntimeError("This should never happen.") from exc
        url = unit_episodes[-1][-1][-1][-1]["url"]
        for unit, episodes in iterator:
            if episodes[-1][-1]["url"] != url:
                yield url, unit_episodes
                url, unit_episodes = episodes[-1][-1]["url"], []
            unit_episodes.append((unit, episodes))
        yield url, unit_episodes

    visualize = _visualize

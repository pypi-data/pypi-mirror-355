"""Google Reverse Geocoding Data."""

from dataclasses import dataclass, field

from mashumaro.mixins.json import DataClassJSONMixin


@dataclass
class LatLng(DataClassJSONMixin):
    """Geographical coordinate with latitude and longitude."""

    latitude: float
    longitude: float


@dataclass
class Viewport(DataClassJSONMixin):
    """Defines a rectangular area using low and high LatLng corners."""

    low: LatLng
    high: LatLng


@dataclass
class PlusCode(DataClassJSONMixin):
    """Represents a plus code with global and optional compound code."""

    global_code: str = field(metadata={"alias": "globalCode"})
    compound_code: str | None = field(default=None, metadata={"alias": "compoundCode"})


@dataclass
class PostalAddress(DataClassJSONMixin):
    """Structured postal address information."""

    region_code: str = field(metadata={"alias": "regionCode"})
    language_code: str = field(metadata={"alias": "languageCode"})
    postal_code: str = field(metadata={"alias": "postalCode"})
    administrative_area: str | None = field(
        default=None, metadata={"alias": "administrativeArea"}
    )
    locality: str | None = None
    address_lines: list[str] | None = field(
        default=None, metadata={"alias": "addressLines"}
    )


@dataclass
class AddressComponent(DataClassJSONMixin):
    """Single component of an address with localized text and types."""

    types: list[str]
    long_text: str = field(metadata={"alias": "longText"})
    short_text: str = field(metadata={"alias": "shortText"})
    language_code: str | None = field(default=None, metadata={"alias": "languageCode"})


@dataclass
class PostalCodeLocality(DataClassJSONMixin):
    """Locality corresponding to a postal code."""

    text: str
    language_code: str | None = field(default=None, metadata={"alias": "languageCode"})


@dataclass
class ResultEntry(DataClassJSONMixin):
    """Main result entry representing a geographic place."""

    place: str
    place_id: str = field(metadata={"alias": "placeId"})
    location: LatLng
    types: list[str]

    granularity: str | None = None
    formatted_address: str | None = field(
        default=None, metadata={"alias": "formattedAddress"}
    )
    viewport: Viewport | None = None
    bounds: Viewport | None = None
    plus_code: PlusCode | None = field(default=None, metadata={"alias": "plusCode"})
    postal_address: PostalAddress | None = field(
        default=None, metadata={"alias": "postalAddress"}
    )
    address_components: list[AddressComponent] | None = field(
        default=None, metadata={"alias": "addressComponents"}
    )
    postal_code_localities: list[PostalCodeLocality] | None = field(
        default=None, metadata={"alias": "postalCodeLocalities"}
    )


@dataclass
class PlacesResponse(DataClassJSONMixin):
    """Full response returned by the Google Places API."""

    results: list[ResultEntry]
    plus_code: PlusCode | None = field(default=None, metadata={"alias": "plusCode"})

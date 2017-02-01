"""Tests for the stix2 library"""

import datetime
import uuid

import pytest
import pytz

import stix2

amsterdam = pytz.timezone('Europe/Amsterdam')
eastern = pytz.timezone('US/Eastern')
FAKE_TIME = datetime.datetime(2017, 1, 1, 12, 34, 56, tzinfo=pytz.utc)


# Inspired by: http://stackoverflow.com/a/24006251
@pytest.fixture
def clock(monkeypatch):

    class mydatetime(datetime.datetime):
        @classmethod
        def now(cls, tz=None):
            return FAKE_TIME

    monkeypatch.setattr(datetime, 'datetime', mydatetime)


def test_clock(clock):
    assert datetime.datetime.now() == FAKE_TIME


@pytest.fixture
def uuid4(monkeypatch):
    def wrapper():
        data = [0]

        def wrapped():
            data[0] += 1
            return "00000000-0000-0000-0000-00000000%04x" % data[0]

        return wrapped
    monkeypatch.setattr(uuid, "uuid4", wrapper())


def test_my_uuid4_fixture(uuid4):
    assert uuid.uuid4() == "00000000-0000-0000-0000-000000000001"
    assert uuid.uuid4() == "00000000-0000-0000-0000-000000000002"
    assert uuid.uuid4() == "00000000-0000-0000-0000-000000000003"
    for _ in range(256):
        uuid.uuid4()
    assert uuid.uuid4() == "00000000-0000-0000-0000-000000000104"


@pytest.mark.parametrize('dt,timestamp', [
    (datetime.datetime(2017, 1, 1, tzinfo=pytz.utc), '2017-01-01T00:00:00Z'),
    (amsterdam.localize(datetime.datetime(2017, 1, 1)), '2016-12-31T23:00:00Z'),
    (eastern.localize(datetime.datetime(2017, 1, 1, 12, 34, 56)), '2017-01-01T17:34:56Z'),
    (eastern.localize(datetime.datetime(2017, 7, 1)), '2017-07-01T04:00:00Z'),
])
def test_timestamp_formatting(dt, timestamp):
    assert stix2.format_datetime(dt) == timestamp


INDICATOR_ID = "indicator--01234567-89ab-cdef-0123-456789abcdef"
MALWARE_ID = "malware--fedcba98-7654-3210-fedc-ba9876543210"
RELATIONSHIP_ID = "relationship--00000000-1111-2222-3333-444444444444"

# Minimum required args for an Indicator instance
INDICATOR_KWARGS = dict(
    labels=['malicious-activity'],
    pattern="[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']",
)

# Minimum required args for a Malware instance
MALWARE_KWARGS = dict(
    labels=['ransomware'],
    name="Cryptolocker",
)

# Minimum required args for a Relationship instance
RELATIONSHIP_KWARGS = dict(
    relationship_type="indicates",
    source_ref=INDICATOR_ID,
    target_ref=MALWARE_ID,
)


@pytest.fixture
def indicator(uuid4, clock):
    return stix2.Indicator(**INDICATOR_KWARGS)


@pytest.fixture
def malware(uuid4, clock):
    return stix2.Malware(**MALWARE_KWARGS)


@pytest.fixture
def relationship(uuid4, clock):
    return stix2.Relationship(**RELATIONSHIP_KWARGS)


EXPECTED_INDICATOR = """{
    "created": "2017-01-01T00:00:00Z",
    "id": "indicator--01234567-89ab-cdef-0123-456789abcdef",
    "labels": [
        "malicious-activity"
    ],
    "modified": "2017-01-01T00:00:00Z",
    "pattern": "[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']",
    "type": "indicator",
    "valid_from": "1970-01-01T00:00:00Z"
}"""


def test_indicator_with_all_required_fields():
    now = datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=pytz.utc)
    epoch = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=pytz.utc)

    indicator = stix2.Indicator(
        type="indicator",
        id=INDICATOR_ID,
        labels=['malicious-activity'],
        pattern="[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']",
        created=now,
        modified=now,
        valid_from=epoch,
    )

    assert str(indicator) == EXPECTED_INDICATOR


def test_indicator_autogenerated_fields(indicator):
    assert indicator.type == 'indicator'
    assert indicator.id == 'indicator--00000000-0000-0000-0000-000000000001'
    assert indicator.created == FAKE_TIME
    assert indicator.modified == FAKE_TIME
    assert indicator.labels == ['malicious-activity']
    assert indicator.pattern == "[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']"
    assert indicator.valid_from == FAKE_TIME

    assert indicator['type'] == 'indicator'
    assert indicator['id'] == 'indicator--00000000-0000-0000-0000-000000000001'
    assert indicator['created'] == FAKE_TIME
    assert indicator['modified'] == FAKE_TIME
    assert indicator['labels'] == ['malicious-activity']
    assert indicator['pattern'] == "[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']"
    assert indicator['valid_from'] == FAKE_TIME


def test_indicator_type_must_be_indicator():
    with pytest.raises(ValueError) as excinfo:
        indicator = stix2.Indicator(type='xxx')

    assert "Indicator must have type='indicator'." in str(excinfo)


def test_indicator_id_must_start_with_indicator():
    with pytest.raises(ValueError) as excinfo:
        indicator = stix2.Indicator(id='my-prefix--')

    assert "Indicator id values must begin with 'indicator--'." in str(excinfo)


def test_indicator_required_field_labels():
    with pytest.raises(ValueError) as excinfo:
        indicator = stix2.Indicator()
    assert "Missing required field for Indicator: 'labels'." in str(excinfo)


def test_indicator_required_field_pattern():
    with pytest.raises(ValueError) as excinfo:
        # Label is checked first, so make sure that is provided
        indicator = stix2.Indicator(labels=['malicious-activity'])
    assert "Missing required field for Indicator: 'pattern'." in str(excinfo)


def test_cannot_assign_to_indicator_attributes(indicator):
    with pytest.raises(ValueError) as excinfo:
        indicator.valid_from = datetime.datetime.now()

    assert "Cannot modify properties after creation." in str(excinfo)


def test_invalid_kwarg_to_indicator():
    with pytest.raises(TypeError) as excinfo:
        indicator = stix2.Indicator(my_custom_property="foo", **INDICATOR_KWARGS)
    assert "unexpected keyword arguments: ['my_custom_property']" in str(excinfo)


EXPECTED_MALWARE = """{
    "created": "2016-05-12T08:17:27Z",
    "id": "malware--fedcba98-7654-3210-fedc-ba9876543210",
    "labels": [
        "ransomware"
    ],
    "modified": "2016-05-12T08:17:27Z",
    "name": "Cryptolocker",
    "type": "malware"
}"""


def test_malware_with_all_required_fields():
    now = datetime.datetime(2016, 5, 12, 8, 17, 27, tzinfo=pytz.utc)

    malware = stix2.Malware(
        type="malware",
        id=MALWARE_ID,
        created=now,
        modified=now,
        labels=["ransomware"],
        name="Cryptolocker",
    )

    assert str(malware) == EXPECTED_MALWARE


def test_malware_autogenerated_fields(malware):
    assert malware.type == 'malware'
    assert malware.id == 'malware--00000000-0000-0000-0000-000000000001'
    assert malware.created == FAKE_TIME
    assert malware.modified == FAKE_TIME
    assert malware.labels == ['ransomware']
    assert malware.name == "Cryptolocker"

    assert malware['type'] == 'malware'
    assert malware['id'] == 'malware--00000000-0000-0000-0000-000000000001'
    assert malware['created'] == FAKE_TIME
    assert malware['modified'] == FAKE_TIME
    assert malware['labels'] == ['ransomware']
    assert malware['name'] == "Cryptolocker"


def test_malware_type_must_be_malware():
    with pytest.raises(ValueError) as excinfo:
        malware = stix2.Malware(type='xxx')

    assert "Malware must have type='malware'." in str(excinfo)


def test_malware_id_must_start_with_malware():
    with pytest.raises(ValueError) as excinfo:
        malware = stix2.Malware(id='my-prefix--')

    assert "Malware id values must begin with 'malware--'." in str(excinfo)


def test_malware_required_field_labels():
    with pytest.raises(ValueError) as excinfo:
        malware = stix2.Malware()
    assert "Missing required field for Malware: 'labels'." in str(excinfo)


def test_malware_required_field_name():
    with pytest.raises(ValueError) as excinfo:
        # Label is checked first, so make sure that is provided
        malware = stix2.Malware(labels=['ransomware'])
    assert "Missing required field for Malware: 'name'." in str(excinfo)


def test_cannot_assign_to_malware_attributes(malware):
    with pytest.raises(ValueError) as excinfo:
        malware.name = "Cryptolocker II"

    assert "Cannot modify properties after creation." in str(excinfo)


def test_invalid_kwarg_to_malware():
    with pytest.raises(TypeError) as excinfo:
        malware = stix2.Malware(my_custom_property="foo", **MALWARE_KWARGS)
    assert "unexpected keyword arguments: ['my_custom_property']" in str(excinfo)


EXPECTED_RELATIONSHIP = """{
    "created": "2016-04-06T20:06:37Z",
    "id": "relationship--00000000-1111-2222-3333-444444444444",
    "modified": "2016-04-06T20:06:37Z",
    "relationship_type": "indicates",
    "source_ref": "indicator--01234567-89ab-cdef-0123-456789abcdef",
    "target_ref": "malware--fedcba98-7654-3210-fedc-ba9876543210",
    "type": "relationship"
}"""


def test_relationship_all_required_fields():
    now = datetime.datetime(2016, 4, 6, 20, 6, 37, tzinfo=pytz.utc)

    relationship = stix2.Relationship(
        type='relationship',
        id=RELATIONSHIP_ID,
        created=now,
        modified=now,
        relationship_type='indicates',
        source_ref=INDICATOR_ID,
        target_ref=MALWARE_ID,
    )
    assert str(relationship) == EXPECTED_RELATIONSHIP


def test_relationship_autogenerated_fields(relationship):
    assert relationship.type == 'relationship'
    assert relationship.id == 'relationship--00000000-0000-0000-0000-000000000001'
    assert relationship.created == FAKE_TIME
    assert relationship.modified == FAKE_TIME
    assert relationship.relationship_type == 'indicates'
    assert relationship.source_ref == INDICATOR_ID
    assert relationship.target_ref == MALWARE_ID

    assert relationship['type'] == 'relationship'
    assert relationship['id'] == 'relationship--00000000-0000-0000-0000-000000000001'
    assert relationship['created'] == FAKE_TIME
    assert relationship['modified'] == FAKE_TIME
    assert relationship['relationship_type'] == 'indicates'
    assert relationship['source_ref'] == INDICATOR_ID
    assert relationship['target_ref'] == MALWARE_ID


def test_relationship_type_must_be_relationship():
    with pytest.raises(ValueError) as excinfo:
        relationship = stix2.Relationship(type='xxx')

    assert "Relationship must have type='relationship'." in str(excinfo)


def test_relationship_id_must_start_with_relationship():
    with pytest.raises(ValueError) as excinfo:
        relationship = stix2.Relationship(id='my-prefix--')

    assert "Relationship id values must begin with 'relationship--'." in str(excinfo)


def test_relationship_required_field_relationship_type():
    with pytest.raises(ValueError) as excinfo:
        relationship = stix2.Relationship()
    assert "Missing required field for Relationship: 'relationship_type'." in str(excinfo)


def test_relationship_required_field_source_ref():
    with pytest.raises(ValueError) as excinfo:
        # relationship_type is checked first, so make sure that is provided
        relationship = stix2.Relationship(relationship_type='indicates')
    assert "Missing required field for Relationship: 'source_ref'." in str(excinfo)


def test_relationship_required_field_target_ref():
    with pytest.raises(ValueError) as excinfo:
        # relationship_type and source_ref are checked first, so make sure those are provided
        relationship = stix2.Relationship(
            relationship_type='indicates',
            source_ref=INDICATOR_ID
        )
    assert "Missing required field for Relationship: 'target_ref'." in str(excinfo)


def test_cannot_assign_to_relationship_attributes(relationship):
    with pytest.raises(ValueError) as excinfo:
        relationship.relationship_type = "derived-from"

    assert "Cannot modify properties after creation." in str(excinfo)


def test_invalid_kwarg_to_relationship():
    with pytest.raises(TypeError) as excinfo:
        relationship = stix2.Relationship(my_custom_property="foo", **RELATIONSHIP_KWARGS)
    assert "unexpected keyword arguments: ['my_custom_property']" in str(excinfo)


def test_create_relationship_from_objects_rather_than_ids(indicator, malware):
    relationship = stix2.Relationship(
        relationship_type="indicates",
        source_ref=indicator,
        target_ref=malware,
    )

    assert relationship.relationship_type == 'indicates'
    assert relationship.source_ref == 'indicator--00000000-0000-0000-0000-000000000001'
    assert relationship.target_ref == 'malware--00000000-0000-0000-0000-000000000002'
    assert relationship.id == 'relationship--00000000-0000-0000-0000-000000000003'


def test_create_relationship_with_positional_args(indicator, malware):
    relationship = stix2.Relationship(indicator, 'indicates', malware)

    assert relationship.relationship_type == 'indicates'
    assert relationship.source_ref == 'indicator--00000000-0000-0000-0000-000000000001'
    assert relationship.target_ref == 'malware--00000000-0000-0000-0000-000000000002'
    assert relationship.id == 'relationship--00000000-0000-0000-0000-000000000003'


EXPECTED_BUNDLE = """{
    "id": "bundle--00000000-0000-0000-0000-000000000004",
    "objects": [
        {
            "created": "2017-01-01T12:34:56Z",
            "id": "indicator--00000000-0000-0000-0000-000000000001",
            "labels": [
                "malicious-activity"
            ],
            "modified": "2017-01-01T12:34:56Z",
            "pattern": "[file:hashes.MD5 = 'd41d8cd98f00b204e9800998ecf8427e']",
            "type": "indicator",
            "valid_from": "2017-01-01T12:34:56Z"
        },
        {
            "created": "2017-01-01T12:34:56Z",
            "id": "malware--00000000-0000-0000-0000-000000000002",
            "labels": [
                "ransomware"
            ],
            "modified": "2017-01-01T12:34:56Z",
            "name": "Cryptolocker",
            "type": "malware"
        },
        {
            "created": "2017-01-01T12:34:56Z",
            "id": "relationship--00000000-0000-0000-0000-000000000003",
            "modified": "2017-01-01T12:34:56Z",
            "relationship_type": "indicates",
            "source_ref": "indicator--01234567-89ab-cdef-0123-456789abcdef",
            "target_ref": "malware--fedcba98-7654-3210-fedc-ba9876543210",
            "type": "relationship"
        }
    ],
    "spec_version": "2.0",
    "type": "bundle"
}"""


def test_empty_bundle():
    bundle = stix2.Bundle()

    assert bundle.type == "bundle"
    assert bundle.id.startswith("bundle--")
    assert bundle.spec_version == "2.0"


def test_bundle_with_wrong_type():
    with pytest.raises(ValueError) as excinfo:
        bundle = stix2.Bundle(type="not-a-bundle")

    assert "Bundle must have type='bundle'." in str(excinfo)


def test_bundle_id_must_start_with_bundle():
    with pytest.raises(ValueError) as excinfo:
        bundle = stix2.Bundle(id='my-prefix--')

    assert "Bundle id values must begin with 'bundle--'." in str(excinfo)


def test_bundle_with_wrong_spec_version():
    with pytest.raises(ValueError) as excinfo:
        bundle = stix2.Bundle(spec_version="1.2")

    assert "Bundle must have spec_version='2.0'." in str(excinfo)


def test_create_bundle(indicator, malware, relationship):
    bundle = stix2.Bundle(objects=[indicator, malware, relationship])

    assert str(bundle) == EXPECTED_BUNDLE

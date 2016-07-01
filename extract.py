#!/usr/bin/env python3

import datetime
import os
import pytz
import re

import icalendar
import jinja2
import openpyxl
import titlecase
import yaml

DIRECTORY = "data"
ICS_PATH = "fireworks.ics"
DATE_RE = re.compile("(January|February|March|April|May|June|July|August|"
                     "September|October|November|December) "
                     "([0-9]{1,2}(?:, [0-9]{1,2})*)(?:st|nd|rd|th)?, "
                     "(20[0-9]{2})", re.I)
TIMEZONE = pytz.timezone("US/Central")


def maybe_titlecase(val):
    if val is None:
        return val
    else:
        return titlecase.titlecase(val)


class Permit(object):
    def __init__(self, number, name, description, address, comment):
        self.number = number
        self.name = maybe_titlecase(name)
        self.description = description
        self.address = maybe_titlecase(address)
        if self.address and "MINNEAPOLIS" not in self.address.upper():
            self.address = self.address + ", Minneapolis, MN"
        self.comment = comment

    def __eq__(self, other):
        return (self.number, self.name, self.description, self.address,
                self.comment) == (other.number, other.name, other.description,
                                  other.address, other.comment)

    def __lt__(self, other):
        return (self.number, self.name, self.description, self.address,
                self.comment) < (other.number, other.name, other.description,
                                 other.address, other.comment)

    def __hash__(self):
        return hash((self.number, self.name, self.description, self.address,
                     self.comment))

    def dates_iter(self):
        for match in DATE_RE.finditer(self.comment):
            month = match.group(1)
            dates = match.group(2)
            year = match.group(3)
            for date in dates.split(", "):
                string = "%s %s %s" % (month, date, year)
                yield datetime.datetime.strptime(string, "%B %d %Y").date()

    def event_iter(self):
        for i, date in enumerate(self.dates_iter()):
            uid = ("fireworks-%s-%d@davidsherenowitsa.party" %
                   (self.number, i))
            yield Event(uid, self.name, date, self.address, self.comment)

    def __str__(self):
        return "%s, \"%s\", \"%s\", \"%s\"" % (self.number,
                                               self.name,
                                               self.address,
                                               self.comment)


class Event(object):
    def __init__(self, uid, name, date, address, comment):
        self.uid = uid
        self.name = name
        self.date = date
        self.address = address
        self.comment = comment

    def to_ical(self):
        event = icalendar.Event()
        event.add("uid", self.uid)
        event.add("summary", "Fireworks: %s" % self.name)
        event.add("dtstart", self.date)
        event.add("dtend", self.date)
        event.add("location", self.address)
        event.add("description", self.comment)
        return event

    def __str__(self):
        return "%s, \"%s\", %s, \"%s\", \"%s\"" % (self.uid,
                                                   self.name,
                                                   self.date,
                                                   self.address,
                                                   self.comment)

    def __lt__(self, other):
        if self.date != other.date:
            return self.date < other.date
        else:
            return self.uid < other.uid


def is_blank_row(row):
    for cell in row:
        if cell.value is not None:
            return False
    return True


def text_lookup(cell):
    value = cell.value
    if value is None:
        return None
    else:
        return re.sub("\\s+", " ", str(value)).strip()


def parse_spreadsheet(path):
    workbook = openpyxl.load_workbook(path)
    worksheet = workbook.active

    header_row = [text_lookup(cell) for cell in worksheet.rows[1]]
    if path.endswith("201606.xlsx"):
        number_index = header_row.index("Permit Number")
        name_index = header_row.index("Permit Name")
        description_index = header_row.index("Description")
        address_index = header_row.index("Permit Street Address")
        comment_index = header_row.index("Comment Text")
    elif path.endswith("201607.xlsx"):
        number_index = header_row.index("Permit#")
        name_index = header_row.index("Event")
        description_index = None
        address_index = None
        comment_index = header_row.index("Event Details")

    for row in worksheet.rows[2:]:
        if is_blank_row(row):
            continue
        permit_number = text_lookup(row[number_index])
        permit_name = text_lookup(row[name_index])
        permit_comment = text_lookup(row[comment_index])
        if description_index:
            permit_description = text_lookup(row[description_index])
        else:
            permit_description = None
        if address_index:
            permit_address = text_lookup(row[address_index])
        elif permit_comment:
            match = re.search("THE EVENT ADDRESS: ([^.]+)\\. THE EVENT",
                              permit_comment)
            if match:
                permit_address = match.group(1)
            else:
                permit_address = None
        else:
            permit_address = None
        permit = Permit(permit_number,
                        permit_name,
                        permit_description,
                        permit_address,
                        permit_comment)
        yield permit


def filter_unwanted_permits(permits):
    for permit in permits:
        if (permit.description == "FIREWORKS DISPLAY - ONE TIME" and
                "INDOOR" in permit.comment):
            continue
        if permit.number == "165175":
            # only a permit for temporary LP, etc.
            # this data production didn't include a proper description column
            continue
        else:
            yield permit


def parse_data():
    for f in os.listdir(DIRECTORY):
        path = os.path.join(DIRECTORY, f)
        if os.path.isfile(path) and path.endswith(".xlsx"):
            yield from filter_unwanted_permits(parse_spreadsheet(path))


def deduplicate(permits):
    return sorted(set(permits))


def write_icalendar(events):
    cal = icalendar.Calendar()
    cal.add("prodid", "-//Fireworks in Minneapolis//davidsherenowitsa.party//")
    cal.add("version", "1.0")
    cal.add("summary", "Fireworks in Minneapolis")
    for event in events:
        cal.add_component(event.to_ical())
    ics_file = open(ICS_PATH, "wb")
    ics_file.write(cal.to_ical())
    ics_file.close()


def write_html(events):
    today = datetime.date.today()
    end_date = datetime.date.today() + datetime.timedelta(days=31)
    loader = jinja2.FileSystemLoader("templates")
    env = jinja2.Environment(loader=loader, autoescape=True)
    template = env.get_template("index.html")
    stream = template.stream(events=events, today=today, end_date=end_date)
    stream.dump("index.html")


def permits_to_events(permits):
    for permit in permits:
        yield from permit.event_iter()


def load_extra_events():
    data = yaml.load(open(os.path.join(DIRECTORY, "other.yaml")))
    for id_, obj in data.items():
        uid = "fireworks-%s@davidsherenowitsa.party" % id_
        date = datetime.datetime.strptime(obj["date"], "%Y-%m-%d").date()
        yield Event(uid, obj["name"], date, obj["address"], obj["comment"])


def main():
    permits = deduplicate(parse_data())

    print("Permits:")
    for permit in permits:
        print(permit)
    print()

    events = list(permits_to_events(permits)) + list(load_extra_events())
    events.sort()

    print("Events:")
    for event in events:
        print(event)

    write_icalendar(events)
    write_html(events)

if __name__ == "__main__":
    main()

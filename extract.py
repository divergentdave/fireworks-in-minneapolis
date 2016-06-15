#!/usr/bin/env python3

import datetime
import os
import pytz
import re

import icalendar
import jinja2
import openpyxl
import titlecase

DIRECTORY = "data"
ICS_PATH = "fireworks.ics"
DATE_RE = re.compile("(January|February|March|April|May|June|July|August|"
                     "September|October|November|December) "
                     "([0-9]{1,2}(?:, [0-9]{1,2})*), (20[0-9]{2})", re.I)
TIMEZONE = pytz.timezone("US/Central")


class Permit(object):
    def __init__(self, number, name, description, address, comment):
        self.number = number
        self.name = titlecase.titlecase(name)
        self.description = description
        self.address = titlecase.titlecase(address)
        if "MINNEAPOLIS" not in self.address.upper():
            self.address = self.address + ", Minneapolis, MN"
        self.comment = comment

    def dates_iter(self):
        for match in DATE_RE.finditer(self.comment):
            month = match.group(1)
            dates = match.group(2)
            year = match.group(3)
            for date in dates.split(", "):
                string = "%s %s %s" % (month, date, year)
                yield datetime.datetime.strptime(string, "%B %d %Y").date()

    def ical_event_iter(self):
        for i, date in enumerate(self.dates_iter()):
            event = icalendar.Event()
            uid = ("fireworks-%s-%d@davidsherenowitsa.party" %
                   (self.number, i))
            event.add("uid", uid)
            event.add("summary", "Fireworks: %s" % self.name)
            event.add("dtstart", date)
            event.add("dtend", date)
            event.add("location", self.address)
            event.add("description", self.comment)
            yield event

    def __str__(self):
        return "%s, \"%s\", \"%s\", \"%s\"" % (self.number,
                                               self.name,
                                               self.address,
                                               self.comment)


def is_blank_row(row):
    for cell in row:
        if cell.value is not None:
            return False
    return True


def parse_spreadsheet(path):
    workbook = openpyxl.load_workbook(path)
    worksheet = workbook.active

    number_index = None
    name_index = None
    description_index = None
    address_index = None
    comment_index = None

    for i, cell in enumerate(worksheet.rows[1]):
        if cell.value:
            text = cell.value.strip()
            if text == "Permit Number":
                number_index = i
            elif text == "Permit Name":
                name_index = i
            elif text == "Description":
                description_index = i
            elif text == "Permit Street Address":
                address_index = i
            elif text == "Comment Text":
                comment_index = i

    for row in worksheet.rows[2:]:
        if is_blank_row(row):
            continue

        def text_lookup(index):
            value = row[index].value
            if value is None:
                return None
            else:
                return re.sub("\\s+", " ", value).strip()

        permit = Permit(text_lookup(number_index),
                        text_lookup(name_index),
                        text_lookup(description_index),
                        text_lookup(address_index),
                        text_lookup(comment_index))
        if permit.description == "FIREWORKS DISPLAY - ONE TIME":
            if "INDOOR" in permit.comment:
                continue
        yield permit


def parse_data():
    for f in os.listdir(DIRECTORY):
        path = os.path.join(DIRECTORY, f)
        if os.path.isfile(path) and path.endswith(".xlsx"):
            yield from parse_spreadsheet(path)


def write_icalendar(permits):
    cal = icalendar.Calendar()
    cal.add("prodid", "-//Fireworks in Minneapolis//davidsherenowitsa.party//")
    cal.add("version", "1.0")
    cal.add("summary", "Fireworks in Minneapolis")
    for permit in permits:
        for event in permit.ical_event_iter():
            cal.add_component(event)
    ics_file = open(ICS_PATH, "wb")
    ics_file.write(cal.to_ical())
    ics_file.close()


def write_html(permits):
    loader = jinja2.FileSystemLoader("templates")
    env = jinja2.Environment(loader=loader, autoescape=True)
    template = env.get_template("index.html")
    template.stream(permits=permits).dump("index.html")


def main():
    permits = parse_data()
    write_icalendar(permits)
    write_html(permits)

if __name__ == "__main__":
    main()

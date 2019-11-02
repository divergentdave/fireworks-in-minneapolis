#!/usr/bin/env python3

import datetime
import os

import icalendar
import jinja2
import yaml

DIRECTORY = "data"
ICS_PATH = "fireworks.ics"


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
    upcoming_events = [event for event in events
                       if event.date >= today and event.date < end_date]
    stream = template.stream(events=upcoming_events)
    stream.dump("index.html")


def load_extra_events():
    data = yaml.load(open(os.path.join(DIRECTORY, "other.yaml")))
    for id_, obj in data.items():
        uid = "fireworks-%s@davidsherenowitsa.party" % id_
        date = datetime.datetime.strptime(obj["date"], "%Y-%m-%d").date()
        yield Event(uid, obj["name"], date, obj["address"], obj["comment"])


def main():
    events = sorted(load_extra_events())

    print("Events:")
    for event in events:
        print(event)

    write_icalendar(events)
    write_html(events)


if __name__ == "__main__":
    main()

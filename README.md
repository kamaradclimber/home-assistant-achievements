# home-assistant-achievements

This is a prototype to have a system of achievements in Home Assistant.

* Short term goal: expose interesting patterns of an HA instance represented as achievements.
* Long term goal: offer a system for any integration to expose achievements easily thanks to helper provided by this repository.
* All time goal: have fun and pride with useless trivia about an HA instance

## Installation

You can install this as a custom repository with HACS.

## Bank of achievements ideas

See achievements.md file (spoiler alert!).

## Design

The integration has two parts:
- a core, listening to events announcing achievemnts, storing them on disk and exposing sensors for each.
- a event emitter with a few demonstration achievements

Technically both could be separated in their own integration. Any integration can provide achievements by sending [an event](https://www.home-assistant.io/docs/configuration/events/) named `achievement_granted`.

The core is listening to event whose data field is:
```
{ "major_version": 0, "minor_version": 1, "achievement": <data> }
```
where `achievement` field depends on the major/minor version.

Here is the format for now:

```
{
  "major_version": 0,
  "minor_version": 1,
  "achievement": {
    "title": <a string giving a catchy name>,
    "description": <a markdown string describing how the achievement was obtained>,
    "source": <a name of the integration which granted the achievemnt>,
    "id": <a string identifying uniquely this achievement, can be reuse if this achievement is granted several times>,
    "granted_on": <optional string giving time at which the event leading to achievement grant happened. If unspecified it is the time of the event. Format is %Y-%m-%dT%H:%M:%S%z>,
    "extra": <optional dictionnary which will be merged with the achievement sensor attribute>
  }
```

## Known integration providing achievements

- [Geovelo](https://github.com/kamaradclimber/geovelo-homeassistant)

# home-assistant-achievements

This is a prototype to have a system of achievements in Home Assistant.

* Short term goal: expose interesting patterns of an HA instance represented as achievements.
* Long term goal: offer a system for any integration to expose achievements easily thanks to helper provided by this repository.
* All time goal: have fun and pride with useless trivia about an HA instance

## Bank of achievements ideas

[ ] Can't choose: have both zigbee and zwave devices
[x] Collector: have more than 50 custom integrations
[ ] Top 10: be in the top 95 percentile for number of integrations used
[ ] Virgin: 0 automation
[ ] Disciple: 1-10 automations
[ ] Crafter: 10-50 automations
[ ] Go home safe: cycle during on the night of New Year's eve
[ ] Out of date: >= 10 pending updates
[x] Dangerous living: upgrade from one beta to another (2024.1b to 2024.2b for instance)
[ ] The more the merrier: have more than 5 users with mobile devices
[ ] Local only: have no integration that does cloud poll/push
[ ] Supporter: enable Home Assistant Cloud
[ ] Autonomous: consumes 0kWh from the grid (all comes from solar or battery)
[ ] Mostly-green: >95% of low carbon energy consumed over a week

## Design

The integration has two parts:
- a core, listening to events announcing achievemnts, storing them on disk and exposing sensors for each.
- a event emitter with a few demonstration achievements

Technically both could be separated in their own integration. Any integration can provide achievements by sending [an event](https://www.home-assistant.io/docs/configuration/events/) named `achievement_granted`.

The core is listening to event whose data field is:
```
{ "major_version": 1, "minor_version": 0, "achievement": <data> }
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

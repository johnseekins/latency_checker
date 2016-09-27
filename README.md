# latency_checker
Simple latency checker in python

Relies on cron for continuous execution, and packs results for shipping to a metrics endpoint in Graphite's [line protocol](http://graphite.readthedocs.io/en/latest/feeding-carbon.html#the-plaintext-protocol) format.

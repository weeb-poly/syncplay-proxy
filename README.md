# Syncplay Proxy

## What does it do

Syncplay Proxy handles STARTTLS negotiation for Syncplay while proxying the traffic back to an internal Syncplay server.
It also provides a WebSocket Endpoint so that Syncplay could theoretically be accessed from the browser.

## What it doesn't do

This isn't a Syncplay server, it just acts as a MITM.
The proxy is not transparent since twisted doesn't have an easy way to do this.

## Authors (Syncplay)

* Initial concept and core internals developer - Uriziel
* GUI design and current lead developer - Et0h
* Original Syncplay code - Tomasz Kowalczyk (Fluxid), who developed [SyncPlay](https://github.com/fluxid/syncplay)
* [Other contributors](http://syncplay.pl/about/development/)

# AnkiTunes

AnkiTunes is an unimaginatively named addon to help you practice traditional tunes.

![Screenshot of Anki with ankitunes installed](https://github.com/akdor1154/ankitunes/blob/master/docs/screenshot.jpg?raw=true)

It lives on [GitHub](https://github.com/akdor1154/ankitunes), and may also be found on the [AnkiWeb Addons site](https://ankiweb.net/shared/info/1456964007).


## Features

 - Store your tunes as ABC, view them as notation
 - Compiles sets of tunes for you to practice - I find this helps me recall tunes better than playing them individually
 - Quickly add new tunes by pasting in URLs from [thesession.org](https://thesession.org)
 - Pre-configures Anki with some nice defaults related to learning tunes (the defaults are more suited for learning masses of little things, e.g. language vocab)


## Usage

### Practice your tunes!
The add-on sets up a deck called "Tunes" for you and adds a couple of reels: If you click on "Tunes", you'll see there are two tunes already there.

If you click **Study Now**, you'll practice your new tunes one by one.

If you click **Practice Sets**, the tunes will be put into sets of of tunes of the same type. The sets are normally two tunes, but will sometimes be three or only one.

Anki will prompt you with tune names - when you see the name, play the tune! Once you've played it (or if you've forgotten how it starts...), click "Show Answer", which will show music notation and ask you how hard one of the tunes were. It will track which tunes are easy and which are difficult, and get you to practice the hard ones more often.

### Add more tunes!
To add more tunes, click the "Add" button on the main screen. This will pop up a box where you can fill in the details of a new tune. You can either fill in the details yourself, or you can paste in a URL from thesession.org and it will fetch the details for you.
  - If you paste in the url to just a tune (e.g. https://thesession.org/tunes/20714) then it will fetch a random setting for that tune - some chaos to keep life interesting!
  - If you paste in the url to a specific setting (e.g. https://thesession.org/tunes/20714#setting41112 - you can get these by the little **#** under individual settings on The Session), it will fetch that setting.

If you want to use the **Practice Sets** feature, make sure you fill in the tune type! I need to know if your tunes are jigs, reels, slipjigs, etc so I can put sets of the right meter together.

### Report bugs!
I've been running this myself for a little while so the worst crashes are probably gone, but there are probably still some rough edges - please [open an issue](https://github.com/akdor1154/ankitunes/issues/new/choose) if you find a bug or just want to ask a question.


## Installation

1) Install Anki if you don't already use it: https://apps.ankiweb.net/
2) Install this add-on - go to Tools -> Add-ons, click "Get Add-ons", and paste in the magic number: 1456964007 (or see https://ankiweb.net/shared/info/1456964007)


## Development

See [DEVELOPMENT.md](https://github.com/akdor1154/ankitunes/blob/master/README.md) for details.
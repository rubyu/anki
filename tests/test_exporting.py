# coding: utf-8

import nose, os, tempfile
from anki import Collection as aopen
from anki.exporting import *
from anki.importing import Anki2Importer
from shared import getEmptyDeck

deck = None
ds = None
testDir = os.path.dirname(__file__)

def setup1():
    global deck
    deck = getEmptyDeck()
    f = deck.newNote()
    f['Front'] = u"foo"; f['Back'] = u"bar"; f.tags = ["tag", "tag2"]
    deck.addNote(f)
    # with a different deck
    f = deck.newNote()
    f['Front'] = u"baz"; f['Back'] = u"qux"
    f.model()['did'] = deck.decks.id("new deck")
    deck.addNote(f)

##########################################################################

@nose.with_setup(setup1)
def test_export_anki():
    # create a new deck with its own conf to test conf copying
    did = deck.decks.id("test")
    dobj = deck.decks.get(did)
    confId = deck.decks.confId("newconf")
    conf = deck.decks.getConf(confId)
    conf['new']['perDay'] = 5
    deck.decks.save(conf)
    deck.decks.setConf(dobj, confId)
    # export
    e = AnkiExporter(deck)
    fd, newname = tempfile.mkstemp(prefix="ankitest", suffix=".anki2")
    newname = unicode(newname)
    os.close(fd)
    os.unlink(newname)
    e.exportInto(newname)
    # exporting should not have changed conf for original deck
    conf = deck.decks.confForDid(did)
    assert conf['id'] != 1
    # connect to new deck
    d2 = aopen(newname)
    assert d2.cardCount() == 2
    # as scheduling was reset, should also revert decks to default conf
    did = d2.decks.id("test", create=False)
    assert did
    conf2 = d2.decks.confForDid(did)
    assert conf2['new']['perDay'] == 20
    dobj = d2.decks.get(did)
    # conf should be 1
    assert dobj['conf'] == 1
    # try again, limited to a deck
    fd, newname = tempfile.mkstemp(prefix="ankitest", suffix=".anki2")
    newname = unicode(newname)
    os.close(fd)
    os.unlink(newname)
    e.did = 1
    e.exportInto(newname)
    d2 = aopen(newname)
    assert d2.cardCount() == 1

@nose.with_setup(setup1)
def test_export_ankipkg():
    # add a test file to the media folder
    open(os.path.join(deck.media.dir(), u"今日.mp3"), "w").write("test")
    n = deck.newNote()
    n['Front'] = u'[sound:今日.mp3]'
    deck.addNote(n)
    e = AnkiPackageExporter(deck)
    fd, newname = tempfile.mkstemp(prefix="ankitest", suffix=".apkg")
    newname = unicode(newname)
    os.close(fd)
    os.unlink(newname)
    e.exportInto(newname)

@nose.with_setup(setup1)
def test_export_anki_due():
    deck = getEmptyDeck()
    f = deck.newNote()
    f['Front'] = u"foo"
    deck.addNote(f)
    deck.crt -= 86400*10
    deck.sched.reset()
    c = deck.sched.getCard()
    deck.sched.answerCard(c, 2)
    deck.sched.answerCard(c, 2)
    # should have ivl of 1, due on day 11
    assert c.ivl == 1
    assert c.due == 11
    assert deck.sched.today == 10
    assert c.due - deck.sched.today == 1
    # export
    e = AnkiExporter(deck)
    e.includeSched = True
    fd, newname = tempfile.mkstemp(prefix="ankitest", suffix=".anki2")
    newname = unicode(newname)
    os.close(fd)
    os.unlink(newname)
    e.exportInto(newname)
    # importing into a new deck, the due date should be equivalent
    deck2 = getEmptyDeck()
    imp = Anki2Importer(deck2, newname)
    imp.run()
    c = deck2.getCard(c.id)
    deck2.sched.reset()
    assert c.due - deck2.sched.today == 1

# @nose.with_setup(setup1)
# def test_export_textcard():
#     e = TextCardExporter(deck)
#     f = unicode(tempfile.mkstemp(prefix="ankitest")[1])
#     os.unlink(f)
#     e.exportInto(f)
#     e.includeTags = True
#     e.exportInto(f)

@nose.with_setup(setup1)
def test_export_textnote():
    e = TextNoteExporter(deck)
    fd, f = tempfile.mkstemp(prefix="ankitest")
    f = unicode(f)
    os.close(fd)
    os.unlink(f)
    e.exportInto(f)
    e.includeTags = True
    e.exportInto(f)

def test_exporters():
    assert "*.apkg" in str(exporters())

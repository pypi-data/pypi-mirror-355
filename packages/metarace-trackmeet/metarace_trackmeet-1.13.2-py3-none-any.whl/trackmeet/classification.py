"""Classification/Medal meta-event handler for trackmeet."""

import os
import gi
import logging

gi.require_version("GLib", "2.0")
from gi.repository import GLib

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

gi.require_version("Gdk", "3.0")
from gi.repository import Gdk

import metarace
from metarace import jsonconfig
from metarace import tod
from metarace import strops
from metarace import report

from . import uiutil
from . import scbwin

# temporary
from functools import cmp_to_key

_log = logging.getLogger('classification')
_log.setLevel(logging.DEBUG)

# config version string
EVENT_ID = 'classification-2.1'

# Model columns
COL_BIB = 0
COL_FIRST = 1
COL_LAST = 2
COL_CLUB = 3
COL_COMMENT = 4
COL_PLACE = 5
COL_MEDAL = 6

# scb function key mappings
key_reannounce = 'F4'  # (+CTRL)
key_abort = 'F5'  # (+CTRL)
key_startlist = 'F3'
key_results = 'F4'


class classification:

    def ridercb(self, rider):
        """Rider change notification function"""
        pass

    def eventcb(self, event):
        """Event change notification function"""
        pass

    def standingstr(self, width=None):
        """Return an event status string for reports and scb."""
        return self._standingstat

    def loadconfig(self):
        """Load race config from disk."""
        findsource = False

        cr = jsonconfig.config({
            'event': {
                'id': EVENT_ID,
                'showinfo': True,
                'showcats': False,
                'showevents': '',
                'decisions': [],
                'placesrc': '',
                'medals': ''
            }
        })
        cr.add_section('event')
        if os.path.exists(self.configfile):
            try:
                with open(self.configfile, 'rb') as f:
                    cr.read(f)
            except Exception as e:
                _log.error('Unable to read config: %s', e)
        else:
            _log.info('%r not found, loading defaults', self.configfile)

        if self.event['info'] == 'Omnium':
            # pre-load source events by searching event db unless config'd
            if not cr.get('event', 'placesrc'):
                cr.set('event', 'showcats', True)
                cr.set('event', 'medals', 'Gold Silver Bronze')
                sources = {
                    'Scratch': None,
                    'Tempo': None,
                    'Elimination': None,
                    'Points': None
                }
                mycat = self.event['prefix']
                for e in self.meet.edb:
                    if e['prefix'] == mycat and e['info'] in sources:
                        sources[e['info']] = e['evid']
                        _log.debug('Found event %s for %s', e['evid'],
                                   e['info'])
                if sources['Points'] is not None:
                    _log.debug('Using event %s for classification places',
                               sources['Points'])
                    cr.set('event', 'placesrc',
                           '%s:1-24' % (sources['Points'], ))
                showevts = []
                revevt = {}
                for sid in ('Scratch', 'Tempo', 'Elimination', 'Points'):
                    if sources[sid] is not None:
                        showevts.append(sources[sid])
                        revevt[sources[sid]] = sid
                if showevts:
                    _log.debug('Using %r as show events list', showevts)
                    evtlist = ' '.join(showevts)
                    cr.set('event', 'showevents', evtlist)
                    self.event['depends'] = evtlist
                    for sid in showevts:
                        try:
                            # while here - visit event config to update omnium flag
                            config = self.meet.event_configfile(sid)
                            ecr = jsonconfig.config()
                            ecr.add_section('event')
                            ecr.load(config)
                            ecr.set('event', 'inomnium', True)
                            ecr.set('event', 'showcats', True)
                            stype = revevt[sid]
                            if stype == 'Points':
                                startevid = sources['Scratch']
                                if startevid is not None:
                                    ecr.set('event', 'autospec',
                                            '%s:1-24' % (startevid, ))
                            elif stype in ('Tempo', 'Elimination'):
                                startevid = sources['Points']
                                if startevid is not None:
                                    ecr.set('event', 'autospec',
                                            '%s:1-24' % (startevid, ))
                            _log.debug('Saving event %s config file %s', sid,
                                       config)
                            with metarace.savefile(config) as f:
                                ecr.write(f)
                        except Excpetion as e:
                            _log.error('%s updating config: %s',
                                       e.__class__.__name__, e)
                cr.set('event', 'showinfo', False)
            else:
                _log.debug('Omnium already configured')

        self.update_expander_lbl_cb()
        self.info_expand.set_expanded(
            strops.confopt_bool(cr.get('event', 'showinfo')))
        self.showcats = cr.get_bool('event', 'showcats')

        self.showevents = cr.get('event', 'showevents')
        self.placesrc = cr.get('event', 'placesrc')
        self.medals = cr.get('event', 'medals')
        self.decisions = cr.get('event', 'decisions')
        self.recalculate()  # model is cleared and loaded in recalc
        eid = cr.get('event', 'id')
        if eid and eid != EVENT_ID:
            _log.info('Event config mismatch: %r != %r', eid, EVENT_ID)

    def startlist_report(self, program=False):
        """Return a startlist report."""
        ret = []
        secid = 'ev-' + str(self.evno).translate(strops.WEBFILE_UTRANS)
        sec = report.section(secid)
        sec.nobreak = True
        headvec = [
            'Event', self.evno, ':', self.event['pref'], self.event['info']
        ]
        if not program:
            headvec.append('- Start List')
        sec.heading = ' '.join(headvec)
        lapstring = strops.lapstring(self.event['laps'])
        substr = ' '.join([lapstring, self.event['dist'],
                           self.event['prog']]).strip()
        if substr:
            sec.subheading = substr
        sec.lines = []
        for r in self.riders:
            rno = r[COL_BIB]
            if 't' in self.series:  # Team no hack
                rno = ' '  # force name
            rh = self.meet.rdb.get_rider(rno, self.series)
            rname = ''
            if rh is not None:
                rname = rh.resname()
            sec.lines.append([None, rno, rname, None, None, None])
        ret.append(sec)
        return ret

    def get_startlist(self):
        """Return a list of bibs in the rider model."""
        ret = []
        for r in self.riders:
            ret.append(r[COL_BIB])
        return ' '.join(ret)

    def saveconfig(self):
        """Save race to disk."""
        if self.readonly:
            _log.error('Attempt to save readonly event')
            return
        cw = jsonconfig.config()
        cw.add_section('event')
        cw.set('event', 'showevents', self.showevents)
        cw.set('event', 'placesrc', self.placesrc)
        cw.set('event', 'medals', self.medals)
        cw.set('event', 'decisions', self.decisions)
        cw.set('event', 'showinfo', self.info_expand.get_expanded())
        cw.set('event', 'showcats', self.showcats)
        cw.set('event', 'id', EVENT_ID)
        _log.debug('Saving event config %r', self.configfile)
        with metarace.savefile(self.configfile) as f:
            cw.write(f)

    def result_gen(self):
        """Generator function to export a final result."""
        for r in self.riders:
            bib = r[COL_BIB]
            rank = None
            info = ''
            rks = r[COL_PLACE]
            if rks:
                if rks.isdigit():
                    rank = int(rks)
                    info = r[COL_MEDAL]
                else:
                    # TODO: allow for 'dnf'/'dns' here, propagates into event
                    rank = rks
                    info = None  # no seeding info available
            time = None

            yield [bib, rank, time, info]

    def result_report(self, recurse=True):  # by default include inners
        """Return a list of report sections containing the race result."""
        ret = []

        # start with the overall result
        secid = 'ev-' + str(self.evno).translate(strops.WEBFILE_UTRANS)
        sec = report.section(secid)
        sec.nobreak = True
        if recurse:
            sec.heading = ' '.join([self.event['pref'],
                                    self.event['info']]).strip()
        else:
            if self.event['evov']:
                sec.heading = ' '.join(
                    [self.event['pref'], self.event['info']]).strip()
            else:
                sec.heading = 'Event ' + self.evno + ': ' + ' '.join(
                    [self.event['pref'], self.event['info']]).strip()
        sec.lines = []
        lapstring = strops.lapstring(self.event['laps'])
        subvec = []
        substr = ' '.join([lapstring, self.event['dist'],
                           self.event['prog']]).strip()
        if substr:
            subvec.append(substr)
        stat = self.standingstr()
        if stat:
            subvec.append(stat)
        if subvec:
            sec.subheading = ' - '.join(subvec)

        prevmedal = ''
        sec.lines = []
        for r in self.riders:
            rno = r[COL_BIB]
            rh = self.meet.rdb.get_rider(rno, self.series)
            rname = ''
            plink = ''
            rcat = ''
            if 't' in self.series:  # Team no hack
                rno = ' '  # force name
                if rh is not None:
                    rname = rh['first']
            else:
                if rh is not None:
                    rname = rh.resname()
                    if rh['uciid']:
                        rcat = rh['uciid']  # overwrite by force

                    # overwrite info if showcats true
                    if self.showcats:
                        rcat = rh.primary_cat()

                    # consider partners here
                    if rh['cat'] and 'tandem' in rh['cat'].lower():
                        ph = self.meet.rdb.get_rider(rh['note'], self.series)
                        if ph is not None:
                            plink = [
                                '', '',
                                ph.resname() + ' - Pilot', ph['uciid'], '', '',
                                ''
                            ]

            rank = ''
            rks = r[COL_PLACE]
            if rks:
                rank = rks
                if rank.isdigit():
                    rank += '.'

            medal = ''
            mds = r[COL_MEDAL]
            if mds:
                medal = mds
            if medal == '' and prevmedal != '':
                # add empty line
                sec.lines.append([None, None, None])
            prevmedal = medal

            nrow = [rank, rno, rname, rcat, None, medal, plink]
            sec.lines.append(nrow)
            if 't' in self.series:
                for trno in strops.riderlist_split(rh['note']):
                    trh = self.meet.rdb.get_rider(trno, self.series)
                    if trh is not None:
                        trname = trh.resname()
                        trinf = trh['uciid']
                        sec.lines.append(
                            [None, trno, trname, trinf, None, None, None])
        ret.append(sec)

        if len(self.decisions) > 0:
            ret.append(self.meet.decision_section(self.decisions))

        if recurse:
            # then append each of the specified events
            for evno in self.showevents.split():
                if evno:
                    _log.debug('Including results from event %r', evno)
                    r = self.meet.get_event(evno, False)
                    if r is None:
                        _log.error('Invalid event %r in showplaces', evno)
                        continue
                    r.loadconfig()  # now have queryable event handle
                    if r.onestart:  # go for result
                        ret.extend(r.result_report())
                    else:  # go for startlist
                        ret.extend(r.startlist_report())
                    r.destroy()
        return ret

    def addrider(self, bib='', place=''):
        """Add specified rider to race model."""
        nr = [bib, '', '', '', '', '', '']
        er = self.getrider(bib)
        if not bib or er is None:
            dbr = self.meet.rdb.get_rider(bib, self.series)
            if dbr is not None:
                nr[1] = dbr['first']
                nr[2] = dbr['last']
                nr[3] = dbr['org']
                nr[4] = dbr['cat']
            nr[COL_PLACE] = place
            return self.riders.append(nr)
        else:
            _log.warning('Rider %r already in model', bib)
            return None

    def getrider(self, bib):
        """Return temporary reference to model row."""
        ret = None
        for r in self.riders:
            if r[COL_BIB] == bib:
                ret = r
                break
        return ret

    def delrider(self, bib):
        """Remove the specified rider from the model."""
        i = self.getiter(bib)
        if i is not None:
            self.riders.remove(i)

    def getiter(self, bib):
        """Return temporary iterator to model row."""
        i = self.riders.get_iter_first()
        while i is not None:
            if self.riders.get_value(i, COL_BIB) == bib:
                break
            i = self.riders.iter_next(i)
        return i

    def recalculate(self):
        """Update internal model."""

        # TODO: update to allow for keirin and sprint inter rounds
        self.riders.clear()

        # Pass one: Create ordered place lookup
        currank = 0
        lookup = {}
        for p in self.placesrc.split(';'):
            placegroup = p.strip()
            if placegroup:
                _log.debug('Adding place group %r at rank %r', placegroup,
                           currank)
                if placegroup == 'X':
                    _log.debug('Added placeholder at rank %r', currank)
                    currank += 1
                else:
                    specvec = placegroup.split(':')
                    if len(specvec) == 2:
                        evno = specvec[0].strip()
                        if evno not in lookup:
                            lookup[evno] = {}
                        if evno != self.evno:
                            placeset = strops.placeset(specvec[1])
                            for i in placeset:
                                lookup[evno][i] = currank
                                currank += 1
                        else:
                            _log.warning('Ignored ref to self %r at rank %r',
                                         placegroup, currank)
                    else:
                        _log.warning('Invalid placegroup %r at rank %r',
                                     placegroup, currank)
            else:
                _log.debug('Empty placegroup at rank %r', currank)

        # Pass 2: create an ordered list of rider numbers using lookup
        placemap = {}
        maxcrank = 0
        for evno in lookup:
            r = self.meet.get_event(evno, False)
            if r is None:
                _log.warning('Event %r not found for lookup %r', evno,
                             lookup[evno])
                return
            r.loadconfig()  # now have queryable event handle
            if r.finished:
                for res in r.result_gen():
                    _log.debug('Result gen %r: %r', evno, res)
                    if isinstance(res[1], int):
                        if res[1] in lookup[evno]:
                            crank = lookup[evno][res[1]] + 1
                            maxcrank = max(maxcrank, crank)
                            _log.debug(
                                'Assigned place %r to rider %r at rank %r',
                                crank, res[0], res[1])
                            if crank not in placemap:
                                placemap[crank] = []
                            placemap[crank].append(res[0])

        # Pass 3: add riders to model in rank order
        i = 1
        while i <= maxcrank:
            if i in placemap:
                for r in placemap[i]:
                    self.addrider(r, str(i))
            i += 1

        if len(self.riders) > 0:  # got at least one result to report
            self.onestart = True
        # Pass 4: Mark medals if required and determine status
        self._standingstat = ''
        medalmap = {}
        placecount = 0
        medalcount = 0
        mplace = 1
        for m in self.medals.split():
            medalmap[mplace] = m
            mplace += 1
        mtotal = len(medalmap)
        for r in self.riders:
            rks = r[COL_PLACE]
            if rks.isdigit():
                rank = int(rks)
                placecount += 1
                if rank in medalmap:
                    r[COL_MEDAL] = medalmap[rank]
                    medalcount += 1
        if placecount > 0:
            if medalcount == mtotal:
                self._standingstat = 'Result'
            elif medalcount > 0:
                self._standingstat = 'Provisional Result'
            else:
                self._standingstat = 'Virtual Standing'
        return

    def key_event(self, widget, event):
        """Race window key press handler."""
        if event.type == Gdk.EventType.KEY_PRESS:
            key = Gdk.keyval_name(event.keyval) or 'None'
            if event.state & Gdk.ModifierType.CONTROL_MASK:
                if key == key_abort or key == key_reannounce:
                    # override ctrl+f5
                    self.recalculate()
                    GLib.idle_add(self.delayed_announce)
                    return True
            elif key[0] == 'F':
                if key == key_startlist:
                    self.do_startlist()
                    GLib.idle_add(self.delayed_announce)
                    return True
                elif key == key_results:
                    self.do_places()
                    GLib.idle_add(self.delayed_announce)
                    return True
        return False

    def delayed_announce(self):
        """Initialise the announcer's screen after a delay."""
        ## TODO because # riders often exceeds 24 - requires paging
        if self.winopen:
            # clear page
            self.meet.txt_clear()
            self.meet.txt_title(' '.join([
                'Event', self.evno, ':', self.event['pref'], self.event['info']
            ]))
            self.meet.txt_line(1)
            self.meet.txt_line(19)

            # write out riders
            lmedal = ''
            posoft = 0
            l = 4
            for r in self.riders:
                if l > 17:
                    l = 4
                    posoft += 41
                plstr = ''
                pls = r[COL_PLACE]
                if pls:
                    plstr = pls
                    if plstr.isdigit():
                        plstr += '.'
                plstr = strops.truncpad(plstr, 3, 'l')
                bibstr = strops.truncpad(r[COL_BIB], 3, 'r')
                clubstr = ''
                tcs = r[COL_CLUB]
                if tcs and len(tcs) <= 3:
                    clubstr = ' (' + tcs + ')'
                namestr = strops.truncpad(
                    strops.fitname(r[COL_FIRST], r[COL_LAST],
                                   25 - len(clubstr)) + clubstr, 25)
                medal = r[COL_MEDAL]
                if lmedal != '' and medal == '':
                    l += 1  # gap to medals
                lmedal = medal
                ol = [plstr, bibstr, namestr, medal]
                self.meet.txt_postxt(l, posoft,
                                     ' '.join([plstr, bibstr, namestr, medal]))
                l += 1

        return False

    def do_startlist(self):
        """Show result on scoreboard."""
        return self.do_places()

    def do_places(self):
        """Show race result on scoreboard."""
        # Draw a 'medal ceremony' on the screen
        resvec = []
        count = 0
        teamnames = False
        name_w = self.meet.scb.linelen - 12
        fmt = [(3, 'l'), (4, 'r'), ' ', (name_w, 'l'), (4, 'r')]
        if self.series and self.series[0].lower() == 't':
            teamnames = True
            name_w = self.meet.scb.linelen - 8
            fmt = [(3, 'l'), ' ', (name_w, 'l'), (4, 'r')]

        for r in self.riders:
            plstr = r[COL_PLACE]
            if plstr.isdigit():
                plstr = plstr + '.'
            no = r[COL_BIB]
            first = r[COL_FIRST]
            last = r[COL_LAST]
            club = r[COL_CLUB]
            if not teamnames:
                resvec.append(
                    [plstr, no,
                     strops.fitname(first, last, name_w), club])
            else:
                resvec.append([plstr, first, club])
            count += 1
        self.meet.scbwin = None
        header = self.meet.racenamecat(self.event)
        ## TODO: Flag Provisional
        evtstatus = 'Final Classification'.upper()
        self.meet.scbwin = scbwin.scbtable(scb=self.meet.scb,
                                           head=self.meet.racenamecat(
                                               self.event),
                                           subhead=evtstatus,
                                           coldesc=fmt,
                                           rows=resvec)
        self.meet.scbwin.reset()
        return False

    def shutdown(self, win=None, msg='Exiting'):
        """Terminate race object."""
        _log.debug('Shutdown event %s: %s', self.evno, msg)
        if not self.readonly:
            self.saveconfig()
        self.winopen = False

    def timercb(self, e):
        """Handle a timer event."""
        return False

    def timeout(self):
        """Update scoreboard and respond to timing events."""
        if not self.winopen:
            return False
        return True

    def do_properties(self):
        """Run race properties dialog."""
        b = uiutil.builder('classification_properties.ui')
        dlg = b.get_object('properties')
        dlg.set_transient_for(self.meet.window)
        se = b.get_object('race_series_entry')
        se.set_text(self.series)
        ee = b.get_object('race_showevents_entry')
        ee.set_text(self.showevents)
        pe = b.get_object('race_placesrc_entry')
        pe.set_text(self.placesrc)
        me = b.get_object('race_medals_entry')
        me.set_text(self.medals)
        response = dlg.run()
        if response == 1:  # id 1 set in glade for "Apply"
            _log.debug('Updating event properties')
            self.placesrc = pe.get_text()
            self.medals = me.get_text()
            self.showevents = ee.get_text()

            # update series
            ns = se.get_text()
            if ns != self.series:
                self.series = ns
                self.event['seri'] = ns

            self.recalculate()
            GLib.idle_add(self.delayed_announce)
        else:
            _log.debug('Edit event properties cancelled')

        # if prefix is empty, grab input focus
        if not self.prefix_ent.get_text():
            self.prefix_ent.grab_focus()
        dlg.destroy()

    def destroy(self):
        """Signal race shutdown."""
        if self.context_menu is not None:
            self.context_menu.destroy()
        self.frame.destroy()

    def show(self):
        """Show race window."""
        self.frame.show()

    def hide(self):
        """Hide race window."""
        self.frame.hide()

    def update_expander_lbl_cb(self):
        """Update race info expander label."""
        self.info_expand.set_label(self.meet.infoline(self.event))

    def editent_cb(self, entry, col):
        """Shared event entry update callback."""
        if col == 'pref':
            self.event['pref'] = entry.get_text()
        elif col == 'info':
            self.event['info'] = entry.get_text()
        self.update_expander_lbl_cb()

    def editcol_db(self, cell, path, new_text, col):
        """Cell update with writeback to meet."""
        new_text = new_text.strip()
        self.riders[path][col] = new_text
        GLib.idle_add(self.meet.rider_edit, self.riders[path][COL_BIB],
                      self.series, col, new_text)

    def __init__(self, meet, event, ui=True):
        """Constructor."""
        self.meet = meet
        self.event = event  # Note: now a treerowref
        self.evno = event['evid']
        self.evtype = event['type']
        self.series = event['seri']
        self.configfile = meet.event_configfile(self.evno)
        _log.debug('Init event %s', self.evno)

        # race run time attributes
        self.onestart = True  # always true for autospec classification
        self.showcats = False  # show primary category on result
        self.readonly = not ui
        self.winopen = ui
        self.placesrc = ''
        self.medals = ''
        self.decisions = []
        self.finished = False
        self._standingstat = ''

        self.riders = Gtk.ListStore(
            str,  # 0 bib
            str,  # 1 first name
            str,  # 2 last name
            str,  # 3 club
            str,  # 4 comment
            str,  # 5 place
            str)  # 6 medal

        b = uiutil.builder('classification.ui')
        self.frame = b.get_object('classification_vbox')
        self.frame.connect('destroy', self.shutdown)

        # info pane
        self.info_expand = b.get_object('info_expand')
        b.get_object('classification_info_evno').set_text(self.evno)
        self.showev = b.get_object('classification_info_evno_show')
        self.prefix_ent = b.get_object('classification_info_prefix')
        self.prefix_ent.set_text(self.event['pref'])
        self.prefix_ent.connect('changed', self.editent_cb, 'pref')
        self.info_ent = b.get_object('classification_info_title')
        self.info_ent.set_text(self.event['info'])
        self.info_ent.connect('changed', self.editent_cb, 'info')

        self.context_menu = None
        if ui:
            # riders pane
            t = Gtk.TreeView(self.riders)
            self.view = t
            t.set_rules_hint(True)

            # riders columns
            uiutil.mkviewcoltxt(t, 'No.', COL_BIB, calign=1.0)
            uiutil.mkviewcoltxt(t,
                                'First Name',
                                COL_FIRST,
                                self.editcol_db,
                                expand=True)
            uiutil.mkviewcoltxt(t,
                                'Last Name',
                                COL_LAST,
                                self.editcol_db,
                                expand=True)
            uiutil.mkviewcoltxt(t, 'Club', COL_CLUB, self.editcol_db)
            uiutil.mkviewcoltxt(t, 'Rank', COL_PLACE, halign=0.5, calign=0.5)
            uiutil.mkviewcoltxt(t, 'Medal', COL_MEDAL)
            t.show()
            b.get_object('classification_result_win').add(t)
            b.connect_signals(self)

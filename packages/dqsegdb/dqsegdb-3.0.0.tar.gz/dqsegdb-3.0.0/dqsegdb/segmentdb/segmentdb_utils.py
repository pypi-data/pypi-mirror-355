# Id$
#
# Copyright (C) 2009  Larne Pekowsky
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# This module was copied from the Grid LSC User Environment (GLUE) where
# it was distributed under the terms of GPL-3.0-or-later.
#

import os
import re
import sys

from . import query_engine
from igwn_ligolw import lsctables
from igwn_ligolw import types as ligolwtypes
from igwn_segments import segment, segmentlist


#
# =============================================================================
#
#                     Routines to set up backends
#
# =============================================================================
#


def get_all_files_in_range(dirname, starttime, endtime, pad=64):
    """Returns all files in dirname and all its subdirectories whose
    names indicate that they contain segments in the range starttime
    to endtime"""

    ret = []

    # Maybe the user just wants one file...
    if os.path.isfile(dirname):
        if re.match(r'.*-[0-9]*-[0-9]*\.xml$', dirname):
            return [dirname]
        else:
            return ret

    first_four_start = starttime // 100000   # noqa: E221
    first_four_end   = endtime   // 100000   # noqa: E221

    # Screen for files starting with . and ending with .xml.*
    # i.e. those leftover by rsync
    file_list = os.listdir(dirname)
    file_list.sort()
    # traverse file_list in reverse order, so that if a filename is removed, the following file is not skipped;
    #   see https://git.ligo.org/computing/dqsegdb/client/-/issues/111
    #   and https://git.ligo.org/lscsoft/glue/-/issues/25
    for filename in file_list[::-1]:
        a = re.match(r"\..*\.xml\..*$", filename)
        if a is not None:
            file_list.remove(a.group(0))

    # for filename in os.listdir(dirname):
    for filename in file_list:
        if re.match(r'.*-[0-9]{5}$', filename):
            dirtime = int(filename[-5:])
            if dirtime >= first_four_start and dirtime <= first_four_end:
                ret += get_all_files_in_range(os.path.join(dirname, filename), starttime, endtime, pad=pad)
        elif re.match(r'.*-[0-9]{4}$', filename):
            dirtime = int(filename[-4:])
            if dirtime >= first_four_start and dirtime <= first_four_end:
                ret += get_all_files_in_range(os.path.join(dirname, filename), starttime, endtime, pad=pad)
        elif re.match(r'.*-[0-9]*-[0-9]*\.xml$', filename):
            file_time = int(filename.split('-')[-2])
            if file_time >= (starttime - pad) and file_time <= (endtime + pad):
                ret.append(os.path.join(dirname, filename))
        elif os.path.isfile(os.path.join(dirname, filename)):
            # Non .xml file, don't recurse:
            return ret
        else:
            # Keep recursing, we may be looking at directories of
            # ifos, each of which has directories with times
            ret += get_all_files_in_range(os.path.join(dirname, filename), starttime, endtime, pad=pad)

    return ret


#
# =============================================================================
#
#        Routines to find segment information in databases/XML docs
#
# =============================================================================
#


def query_segments(engine, table, segdefs):
    # each segdef is a list containing:
    #     ifo, name, version, start_time, end_time, start_pad, end_pad

    # The trivial case: if there's nothing to do, return no time
    if len(segdefs) == 0:
        return [segmentlist([])]

    #
    # For the sake of efficiency we query the database for all the segdefs at once
    # This constructs a clause that looks for one
    #
    def make_clause(table, segdef):
        ifo, name, version, start_time, end_time, start_pad, end_pad = segdef

        sql = " (segment_definer.ifos = '%s' " % ifo
        sql += "AND segment_definer.name = '%s' " % name
        sql += "AND segment_definer.version = %s " % version
        sql += "AND NOT (%d > %s.end_time OR %s.start_time > %d)) " % (start_time, table, table, end_time)

        return sql

    clauses = [make_clause(table, segdef) for segdef in segdefs]

    sql = 'SELECT segment_definer.ifos, segment_definer.name, segment_definer.version, '
    sql += ' %s.start_time, %s.end_time ' % (table, table)
    sql += ' FROM segment_definer, %s ' % table
    sql += ' WHERE %s.segment_def_id = segment_definer.segment_def_id AND ' % table

    if engine.__class__ == query_engine.LdbdQueryEngine:
        sql += " %s.segment_def_cdb = segment_definer.creator_db AND " % table

    sql += '( ' + ' OR '.join(clauses) + ' )'

    rows = engine.query(sql)

    #
    # The result of a query will be rows of the form
    #    ifo, name, version, start_time, end_time
    #
    # We want to associate each returned row with the segdef it belongs to so that
    # we can apply the correct padding.
    #
    # If segdefs were uniquely spcified by (ifo, name, version) this would
    # be easy, but it may happen that we're looking for the same segment definer
    # at multiple disjoint times.  In particular this can happen if the user
    # didn't specify a version number; in that case we might have version 2
    # of some flag defined over multiple disjoint segment_definers.
    #
    results = []

    for segdef in segdefs:
        ifo, name, version, start_time, end_time, start_pad, end_pad = segdef

        search_span = segment(start_time, end_time)
        search_span_list = segmentlist([search_span])

        # See whether the row belongs to the current segdef.  Name, ifo and version must match
        # and the padded segment must overlap with the range of the segdef.
        def matches(row):
            return (row[0].strip() == ifo and row[1] == name and int(row[2]) == int(version)
                    and search_span.intersects(segment(row[3] + start_pad, row[4] + start_pad)))   # noqa: W503

        # Add the padding.  Segments may extend beyond the time of interest, chop off the excess.
        def pad_and_truncate(row_start, row_end):
            tmp = segmentlist([segment(row_start + start_pad, row_end + end_pad)])
            # No coalesce needed as a list with a single segment is already coalesced
            tmp &= search_span_list

            # The intersection is guaranteed to be non-empty if the row passed match()
            # PR 2969: The above comment is incorrect.  Negative padding may cause
            # an empty intersection.
            if len(tmp) == 0:
                return segment(0, 0)
            else:
                return tmp[0]

        # Build a segment list from the returned segments, padded and trunctated.  The segments will
        # not necessarily be disjoint, if the padding crosses gaps.  They are also not gauranteed to
        # be in order, since there's no ORDER BY in the query.  So the list needs to be coalesced
        # before arithmatic can be done with it.
        result = segmentlist([pad_and_truncate(row[3], row[4]) for row in rows if matches(row)]).coalesce()

        # This is not needed: since each of the segments are constrained to be within the search
        # span the whole list must be as well.
        # result &= search_span_list

        results.append(result)

    return results


def expand_version_number(engine, segdef):
    ifo, name, version, start_time, end_time, start_pad, end_pad = segdef

    if version != '*':
        return [segdef]

    # Start looking at the full interval
    intervals = segmentlist([segment(start_time, end_time)])

    # Find the maximum version number
    sql = "SELECT max(version) FROM segment_definer "
    sql += "WHERE  segment_definer.ifos = '%s' " % ifo
    sql += "AND   segment_definer.name = '%s' " % name

    rows = engine.query(sql)
    try:
        version = len(rows[0]) and rows[0][0] or 1
    except:
        version = None

    results = []

    while version > 0:
        for interval in intervals:
            segs = query_segments(engine, 'segment_summary', [(ifo, name, version, interval[0], interval[1], 0, 0)])

            for seg in segs[0]:
                results.append((ifo, name, version, seg[0], seg[1], 0, 0))

        intervals.coalesce()
        intervals -= segs[0]

        version -= 1

    return results


def find_segments(doc, key, use_segment_table=True):
    key_pieces = key.split(':')
    while len(key_pieces) < 3:
        key_pieces.append('*')

    filter_func = lambda x: str(x.ifos) == key_pieces[0] and (str(x.name) == key_pieces[1] or key_pieces[1] == '*') and (str(x.version) == key_pieces[2] or key_pieces[2] == '*')   # noqa: E501

    # Find all segment definers matching the critieria
    seg_def_table = lsctables.SegmentDefTable.get_table(doc)
    seg_defs = list(filter(filter_func, seg_def_table))
    seg_def_ids = [str(x.segment_def_id) for x in seg_defs]

    # Find all segments belonging to those definers
    if use_segment_table:
        seg_table = lsctables.SegmentTable.get_table(doc)
        seg_entries = [x for x in seg_table if str(x.segment_def_id) in seg_def_ids]
    else:
        seg_sum_table = lsctables.SegmentSumTable.get_table(doc)
        seg_entries = [x for x in seg_sum_table if str(x.segment_def_id) in seg_def_ids]

    # Combine into a segmentlist
    ret = segmentlist([segment(x.start_time, x.end_time) for x in seg_entries])

    ret.coalesce()

    return ret


#
# =============================================================================
#
#                      General utilities
#
# =============================================================================
#

def ensure_segment_table(connection):
    """Ensures that the DB represented by connection posses a segment table.
    If not, creates one and prints a warning to stderr"""

    count = connection.cursor().execute("SELECT count(*) FROM sqlite_master WHERE name='segment'").fetchone()[0]

    if count == 0:
        sys.stderr.write("WARNING: None of the loaded files contain a segment table\n")
        theClass = lsctables.TableByName['segment']
        statement = "CREATE TABLE IF NOT EXISTS segment (" + ", ".join(["%s %s" % (key, ligolwtypes.ToSQLiteType[theClass.validcolumns[key]]) for key in theClass.validcolumns]) + ")"   # noqa: E501

        connection.cursor().execute(statement)


# =============================================================================
#
#                    Routines to write data to XML documents
#
# =============================================================================
#

def add_to_segment_definer(xmldoc, proc_id, ifo, name, version, comment=''):
    try:
        seg_def_table = lsctables.SegmentDefTable.get_table(xmldoc)
    except:
        seg_def_table = lsctables.New(lsctables.SegmentDefTable,
                                      columns=["process:process_id", "segment_def_id", "ifos", "name",
                                               "version", "comment"])
        xmldoc.childNodes[0].appendChild(seg_def_table)

    seg_def_id                     = seg_def_table.get_next_id()   # noqa: E221
    segment_definer                = lsctables.SegmentDef()        # noqa: E221
    segment_definer.process_id     = proc_id                       # noqa: E221
    segment_definer.segment_def_id = seg_def_id                    # noqa: E221
    segment_definer.ifos           = ifo                           # noqa: E221
    segment_definer.name           = name                          # noqa: E221
    segment_definer.version        = version                       # noqa: E221
    segment_definer.comment        = comment                       # noqa: E221

    seg_def_table.append(segment_definer)

    return seg_def_id


def add_to_segment(xmldoc, proc_id, seg_def_id, sgmtlist):
    try:
        segtable = lsctables.SegmentTable.get_table(xmldoc)
    except:
        segtable = lsctables.New(lsctables.SegmentTable,
                                 columns=["process:process_id", "segment_definer:segment_def_id", "segment_id",
                                          "start_time", "start_time_ns", "end_time", "end_time_ns"])
        xmldoc.childNodes[0].appendChild(segtable)

    for seg in sgmtlist:
        segment                = lsctables.Segment()      # noqa: E221
        segment.process_id     = proc_id                  # noqa: E221
        segment.segment_def_id = seg_def_id               # noqa: E221
        segment.segment_id     = segtable.get_next_id()   # noqa: E221
        segment.start_time     = seg[0]                   # noqa: E221
        segment.start_time_ns  = 0                        # noqa: E221
        segment.end_time       = seg[1]                   # noqa: E221
        segment.end_time_ns    = 0                        # noqa: E221

        segtable.append(segment)


def add_to_segment_summary(xmldoc, proc_id, seg_def_id, sgmtlist, comment=''):
    try:
        seg_sum_table = lsctables.SegmentSumTable.get_table(xmldoc)
    except:
        seg_sum_table = lsctables.New(lsctables.SegmentSumTable,
                                      columns=["process:process_id", "segment_definer:segment_def_id",
                                               "segment_sum_id", "start_time", "start_time_ns",
                                               "end_time", "end_time_ns", "comment"])
        xmldoc.childNodes[0].appendChild(seg_sum_table)

    for seg in sgmtlist:
        segment_sum                = lsctables.SegmentSum()        # noqa: E221
        segment_sum.process_id     = proc_id                       # noqa: E221
        segment_sum.segment_def_id = seg_def_id                    # noqa: E221
        segment_sum.segment_sum_id = seg_sum_table.get_next_id()   # noqa: E221
        segment_sum.start_time     = seg[0]                        # noqa: E221
        segment_sum.start_time_ns  = 0                             # noqa: E221
        segment_sum.end_time       = seg[1]                        # noqa: E221
        segment_sum.end_time_ns    = 0                             # noqa: E221
        segment_sum.comment        = comment                       # noqa: E221

        seg_sum_table.append(segment_sum)


def add_segment_info(doc, proc_id, segdefs, segments, segment_summaries):

    for i in range(len(segdefs)):
        ifo, name, version, start_time, end_time, start_pad, end_pad = segdefs[i]

        seg_def_id = add_to_segment_definer(doc, proc_id, ifo, name, version)

        add_to_segment_summary(doc, proc_id, seg_def_id, segment_summaries[i])

        if segments:
            add_to_segment(doc, proc_id, seg_def_id, segments[i])

#
# =============================================================================
#
#                      Routines that should be obsolete
#
# =============================================================================
#

# (none right now)
